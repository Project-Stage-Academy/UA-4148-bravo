import html
import os
import re
from collections import OrderedDict
from django.utils.timezone import now
from rest_framework import serializers
from chat.documents import Room, Message
from core.settings.constants import FORBIDDEN_WORDS_SET
from utils.sanitize import sanitize_message

MAX_PARTICIPANTS = int(os.getenv("MAX_PARTICIPANTS", 50))
MIN_MESSAGE_LENGTH = int(os.getenv("MIN_MESSAGE_LENGTH", 1))
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 1000))


class RoomSerializer(serializers.Serializer):
    """
    Serializer for chat rooms.

    Fields:
        - name (str): Name of the room (3–50 characters).
        - is_group (bool): Indicates if the room is a group chat (default=False).
        - participants (list[str]): List of participant emails. Must not be empty.

    Validation:
        - Removes duplicate participants (keeps order).
        - Ensures private rooms have exactly 2 participants.
        - Ensures the number of participants does not exceed MAX_PARTICIPANTS.
    """

    name = serializers.CharField(min_length=3, max_length=50)
    is_group = serializers.BooleanField(default=False)
    participants = serializers.ListField(
        child=serializers.EmailField(), allow_empty=False
    )

    def validate_participants(self, value):
        """
        Validate the participants list.

        - Removes duplicates while preserving order.
        - Ensures the number of participants does not exceed MAX_PARTICIPANTS.
        """
        unique_emails = list(OrderedDict.fromkeys(value))
        if len(unique_emails) > MAX_PARTICIPANTS:
            raise serializers.ValidationError(
                f"Room cannot have more than {MAX_PARTICIPANTS} participants."
            )
        return unique_emails

    def validate_name(self, value):
        """
        Validate and sanitize the room name.

        - Strips leading and trailing whitespace.
        - Escapes HTML characters to prevent XSS attacks.

        Args:
            value (str): The raw room name input.

        Returns:
            str: Sanitized room name safe for storage and display.
        """
        return html.escape(value.strip())

    def validate(self, data):
        """
        Cross-field validation.

        - Ensures private rooms (`is_group=False`) contain exactly 2 participants.
        """
        if not data['is_group'] and len(data['participants']) != 2:
            raise serializers.ValidationError(
                "Private room must have exactly 2 participants."
            )
        return data

    def create(self, validated_data):
        """
        Create and persist a new Room instance.
        """
        room = Room(**validated_data)
        room.save()
        return room

    def update(self, instance, validated_data):
        """
        Update an existing Room instance with validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.is_group = validated_data.get('is_group', instance.is_group)
        instance.participants = validated_data.get('participants', instance.participants)
        instance.save()
        return instance


class MessageSerializer(serializers.Serializer):
    """
    Serializer for chat messages.

    Fields:
        - room (str): The name of the room where the message belongs.
        - sender_email (str): Email of the user sending the message.
        - receiver_email (str, optional): Email of the recipient (required for private messages).
        - text (str): Message content with length restrictions.
        - created_at (datetime): Time of message creation (defaults to current UTC time).
        - is_read (bool): Indicates whether the message has been read.
    """
    room = serializers.CharField()
    sender_email = serializers.EmailField()
    receiver_email = serializers.EmailField(required=False, allow_null=True)
    text = serializers.CharField(
        min_length=MIN_MESSAGE_LENGTH, max_length=MAX_MESSAGE_LENGTH
    )
    created_at = serializers.DateTimeField(default=now)
    is_read = serializers.BooleanField(default=False)

    def validate_text(self, value):
        """
        Validate the content of the message.
        """
        if not value.strip():
            raise serializers.ValidationError("Message text cannot be empty.")

        value = sanitize_message(value)

        lowered = value.lower()
        forbidden_pattern = r'\b(?:' + '|'.join(
            re.escape(word) for word in FORBIDDEN_WORDS_SET
        ) + r')\b'
        if re.search(forbidden_pattern, lowered):
            raise serializers.ValidationError("Message contains forbidden content.")

        if re.search(r"([^aeiou\s])\1{10,}", value, re.IGNORECASE):
            raise serializers.ValidationError("Message looks like spam.")

        return value

    def validate(self, data):
        """
        Cross-field validation for message consistency with the room.
        """
        room_name = data.get('room')
        if not room_name:
            raise serializers.ValidationError("Room name is required.")

        try:
            room = Room.objects.get(name=room_name)
        except Room.DoesNotExist:
            raise serializers.ValidationError("Room does not exist.")

        if data['sender_email'] not in room.participants:
            raise serializers.ValidationError("Sender must be a participant of the room.")

        if room.is_group:
            if data.get('receiver_email') and data['receiver_email'] not in room.participants:
                raise serializers.ValidationError(
                    "Receiver must be a participant of the group."
                )
        else:
            if not data.get('receiver_email'):
                raise serializers.ValidationError(
                    "Receiver is required in private messages."
                )
            if data['receiver_email'] not in room.participants:
                raise serializers.ValidationError(
                    "Receiver must be a participant of the room."
                )

        data['room_instance'] = room
        return data

    def create(self, validated_data):
        """
        Create and persist a new Message instance in the given room.
        """
        room = validated_data.pop('room_instance')
        msg = Message(room=room, **validated_data)
        msg.save()
        return msg

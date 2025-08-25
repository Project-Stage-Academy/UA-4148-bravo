import os
import re
from django.utils.timezone import now
from rest_framework import serializers
from chat.documents import Room, Message
from core.settings.constants import FORBIDDEN_WORDS_SET

MAX_PARTICIPANTS = int(os.getenv("MAX_PARTICIPANTS", 50))
MIN_MESSAGE_LENGTH = int(os.getenv("MIN_MESSAGE_LENGTH", 1))
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 1000))


class RoomSerializer(serializers.Serializer):
    """
    Serializer for chat rooms (conversations).

    Fields:
        - name (str): Unique identifier for the room (3-50 chars, letters, digits, dash, underscore).
        - is_group (bool): Indicates if the room is a group chat (True) or private chat (False).
        - participants (list[str]): List of user IDs participating in the room.

    Validation:
        - Room name must contain only allowed characters.
        - Number of participants must not exceed MAX_PARTICIPANTS.
        - Private rooms must have exactly 2 participants.
    """

    name = serializers.CharField(min_length=3, max_length=50)
    is_group = serializers.BooleanField(default=False)
    participants = serializers.ListField(
        child=serializers.CharField(), allow_empty=False
    )

    def validate_name(self, value):
        """
        Ensure the room name only contains letters, digits, dash, or underscore.
        """
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                "Room name can only contain letters, numbers, dash, underscore."
            )
        return value

    def validate_participants(self, value):
        """
        Ensure participants list contains unique IDs and does not exceed the maximum limit.
        """
        unique_ids = list(set(value))
        if len(unique_ids) > MAX_PARTICIPANTS:
            raise serializers.ValidationError(
                f"Room cannot have more than {MAX_PARTICIPANTS} participants."
            )
        return unique_ids

    def validate(self, data):
        """
        Cross-field validation for the room.
        - Ensures private rooms have exactly 2 participants.
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
        - sender_id (str): ID of the user sending the message.
        - receiver_id (str, optional): ID of the recipient (required for private messages).
        - text (str): Message content (with length restrictions and forbidden words filtering).
        - timestamp (datetime): Time of message creation (defaults to now in UTC).
        - is_read (bool): Indicates if the message has been read.

    Validation:
        - Text must not be empty, contain forbidden words, or spam-like repeated characters.
        - Sender must belong to the room.
        - For private rooms, receiver_id is required and must be the other participant.
        - For group rooms, receiver_id must be a participant if provided.
    """

    room = serializers.CharField()
    sender_id = serializers.CharField()
    receiver_id = serializers.CharField(required=False, allow_null=True)
    text = serializers.CharField(
        min_length=MIN_MESSAGE_LENGTH, max_length=MAX_MESSAGE_LENGTH
    )
    timestamp = serializers.DateTimeField(default=now)
    is_read = serializers.BooleanField(default=False)

    def validate_text(self, value):
        """
        Validate the content of the message.
        """
        if not value.strip():
            raise serializers.ValidationError("Message text cannot be empty.")

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
        try:
            room = Room.objects.get(name=data['room'])
        except Room.DoesNotExist:
            raise serializers.ValidationError("Room does not exist.")

        if data['sender_id'] not in room.participants:
            raise serializers.ValidationError("Sender must be a participant of the room.")

        if room.is_group:
            if data.get('receiver_id') and data['receiver_id'] not in room.participants:
                raise serializers.ValidationError(
                    "Receiver must be a participant of the group."
                )
        else:
            if not data.get('receiver_id'):
                raise serializers.ValidationError(
                    "Receiver is required in private messages."
                )
            if data['receiver_id'] not in room.participants:
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

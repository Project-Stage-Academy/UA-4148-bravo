import logging
from rest_framework import serializers
from chat.documents import Room, Message, MIN_MESSAGE_LENGTH, MAX_MESSAGE_LENGTH
from utils.save_documents import log_and_capture

logger = logging.getLogger(__name__)


class RoomSerializer(serializers.Serializer):
    """
    Serializer for a private chat room (Investor + Startup) with timestamps.
    """
    name = serializers.CharField(min_length=3, max_length=50)
    participants = serializers.ListField(
        child=serializers.EmailField(), allow_empty=False
    )
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    @log_and_capture("room")
    def create(self, validated_data):
        room = Room(**validated_data)
        room.save()
        return room

    @log_and_capture("room")
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.participants = validated_data.get('participants', instance.participants)
        instance.save()
        return instance


class MessageSerializer(serializers.Serializer):
    """
    Serializer for private chat messages exchanged between exactly two participants
    (Investor and Startup) in a Room.
    """

    room_name = serializers.CharField(max_length=50)
    sender_email = serializers.EmailField(read_only=True)
    receiver_email = serializers.EmailField()
    text = serializers.CharField(
        min_length=MIN_MESSAGE_LENGTH,
        max_length=MAX_MESSAGE_LENGTH
    )
    timestamp = serializers.DateTimeField(read_only=True)
    is_read = serializers.BooleanField(default=False)

    @log_and_capture("message")
    def create(self, validated_data):
        """
        Create a Message instance.
        sender_email must be passed via context.
        """
        sender_email = self.context.get("sender_email")
        if not sender_email:
            raise serializers.ValidationError("Sender email must be provided in context.")

        room_name = validated_data.pop("room_name")
        room = Room.objects(name=room_name).first()
        if not room:
            raise serializers.ValidationError(f"Room '{room_name}' does not exist.")

        message = Message(
            room=room,
            sender_email=sender_email,
            **validated_data
        )
        message.save()
        return message

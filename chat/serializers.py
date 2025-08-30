import datetime
import logging
import os
from rest_framework import serializers
from chat.documents import Room, Message
from utils.save_documents import log_and_capture

logger = logging.getLogger(__name__)

MIN_MESSAGE_LENGTH = int(os.getenv("MIN_MESSAGE_LENGTH", 1))
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 1000))


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

    Fields:
        room (str): The name of the Room the message belongs to.
        sender_email (str): Email of the sender.
        receiver_email (str): Email of the receiver (required for private messages).
        text (str): Message content (sanitized and validated).
        timestamp (datetime): UTC timestamp of message creation (defaults to now).
        is_read (bool): Indicates whether the message has been read by the receiver.
    """

    room = serializers.CharField()
    sender_email = serializers.EmailField(read_only=True)
    receiver_email = serializers.EmailField()
    text = serializers.CharField(
        min_length=MIN_MESSAGE_LENGTH, max_length=MAX_MESSAGE_LENGTH
    )
    timestamp = serializers.DateTimeField(default=lambda: datetime.now(datetime.timezone.utc), read_only=True)
    is_read = serializers.BooleanField(default=False)

    @log_and_capture("message")
    def create(self, validated_data):
        room = validated_data.pop('room_instance')
        msg = Message(room=room, **validated_data)
        msg.save()
        return msg

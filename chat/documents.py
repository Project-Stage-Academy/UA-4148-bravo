import os
from mongoengine import CASCADE
from mongoengine import (
    Document, StringField, ListField, ReferenceField,
    DateTimeField, BooleanField, ValidationError
)
from datetime import datetime, timezone
import re
from core.settings.constants import FORBIDDEN_WORDS_SET

MAX_PARTICIPANTS = int(os.getenv("MAX_PARTICIPANTS", 50))
MIN_MESSAGE_LENGTH = int(os.getenv("MIN_MESSAGE_LENGTH", 1))
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 1000))


class Room(Document):
    """
    Represents a chat room in MongoDB storing user emails as participants
    (bridge key to PostgreSQL users).
    """

    NAME_REGEX = r'^[a-zA-Z0-9_-]+$'

    name = StringField(
        required=True,
        min_length=3,
        max_length=50,
        regex=NAME_REGEX,
        unique=True
    )
    is_group = BooleanField(default=False)
    participants = ListField(StringField())  # <-- emails
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {"collection": "rooms"}

    def clean(self):
        """
        Validate room data before saving:
        - Remove duplicate emails.
        - Limit participants to MAX_PARTICIPANTS.
        """
        self.participants = list(dict.fromkeys(self.participants))

        if len(self.participants) > MAX_PARTICIPANTS:
            raise ValidationError(f"Room cannot have more than {MAX_PARTICIPANTS} participants")

    def save(self, *args, **kwargs):
        """ Update the 'updated_at' timestamp before saving. """
        self.updated_at = datetime.now(timezone.utc)
        self.clean()
        return super().save(*args, **kwargs)


class Message(Document):
    """
    Represents a chat message stored in MongoDB using sender and receiver emails.

    Validation rules:
        - Room must exist and be persisted.
        - Sender must be a participant of the room.
        - Private messages: must have exactly 2 participants and a receiver.
        - Group messages: receiver can be None; if specified, must be a participant.
        - Message text cannot be empty.
        - Forbidden words are not allowed.
        - Messages with repeated characters (spam) are rejected.
    """

    room = ReferenceField(Room, required=True, reverse_delete_rule=CASCADE)
    sender_email = StringField(required=True)
    receiver_email = StringField(required=False)
    text = StringField(required=True, min_length=MIN_MESSAGE_LENGTH, max_length=MAX_MESSAGE_LENGTH)
    timestamp = DateTimeField(default=lambda: datetime.now(timezone.utc))
    is_read = BooleanField(default=False)

    def clean(self):
        """ Validate message before saving. """
        if not self.room or not self.room.id:
            raise ValidationError("Message must belong to a persisted room.")

        if self.sender_email not in self.room.participants:
            raise ValidationError("Sender must be a participant of the room.")

        if self.room.is_group:
            if self.receiver_email is not None and self.receiver_email not in self.room.participants:
                raise ValidationError("Receiver must be a participant of the group.")
        else:
            if len(self.room.participants) != 2:
                raise ValidationError("Private room must have exactly 2 participants.")
            if not self.receiver_email:
                raise ValidationError("Receiver is required in private messages.")

        if not self.text.strip():
            raise ValidationError("Message text cannot be empty.")

        lowered = self.text.lower()
        if FORBIDDEN_WORDS_SET:
            forbidden_pattern = r'\b(?:' + '|'.join(re.escape(word) for word in FORBIDDEN_WORDS_SET) + r')\b'
            if re.search(forbidden_pattern, lowered):
                raise ValidationError("Message contains forbidden content.")

        if re.search(r"([^aeiou\s])\1{10,}", self.text, re.IGNORECASE):
            raise ValidationError("Message looks like spam.")

    def save(self, *args, **kwargs):
        """ Update timestamp and clean before saving. """
        self.timestamp = datetime.now(timezone.utc)
        self.clean()
        return super().save(*args, **kwargs)

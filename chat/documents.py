import logging
import os
import re
from datetime import datetime, timezone
from mongoengine import CASCADE
from mongoengine import (
    Document, StringField, ListField, ReferenceField,
    DateTimeField, BooleanField, ValidationError
)
from core.settings.constants import FORBIDDEN_WORDS_SET
from users.models import UserRole
from utils.encrypt import EncryptedStringField
from utils.get_user_or_raise import get_user_or_raise
from utils.sanitize import sanitize_message, sanitize_room_name
import sentry_sdk
from utils.save_documents import log_and_capture

logger = logging.getLogger(__name__)

MIN_MESSAGE_LENGTH = int(os.getenv("MIN_MESSAGE_LENGTH", 1))
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 1000))


class Room(Document):
    """
    Represents a private chat room between exactly two users:
    one Investor and one Startup.
    """

    NAME_REGEX = r'^[a-zA-Z0-9_&;-]+$'

    name = StringField(
        required=True,
        min_length=3,
        max_length=50,
        regex=NAME_REGEX,
        unique=True
    )
    participants = ListField(StringField(), required=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    meta = {
        "collection": "rooms",
        "db_alias": "chat_test"
    }

    def clean(self):
        """Validate that the room has exactly 2 participants (Investor + Startup)."""
        self.participants = list(dict.fromkeys(self.participants))

        if len(self.participants) != 2:
            msg = "Room must have exactly 2 participants (Investor and Startup)."
            logger.warning("[ROOM_VALIDATION] %s | room=%s", msg, self.name)
            sentry_sdk.capture_message(msg, level="warning")
            raise ValidationError(msg)

        users = [get_user_or_raise(email, self.name) for email in self.participants]

        roles = {user.role.role if user.role else None for user in users}
        if roles != {UserRole.Role.INVESTOR, UserRole.Role.STARTUP}:
            msg = "Room must have exactly one Investor and one Startup."
            logger.warning("[ROOM_VALIDATION] %s | participants=%s", msg, self.participants)
            sentry_sdk.capture_message(msg, level="warning")
            raise ValidationError(msg)

        self.name = sanitize_room_name(self.name)

    @log_and_capture("room", ValidationError)
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now(timezone.utc)
        return super().save(*args, **kwargs)


class Message(Document):
    """
    Represents a private chat message exchanged between two users
    (Investor and Startup) inside a `Room`.

    A `Message` belongs to a specific `Room` and is always associated
    with exactly two participants: a sender and a receiver.

    Fields:
        room (Room): Reference to the chat room this message belongs to.
        sender_email (str): Email of the user sending the message.
        receiver_email (str): Email of the user receiving the message.
        text (str): The encrypted message text.
        timestamp (datetime): The UTC datetime when the message was created.
        is_read (bool): Indicates if the receiver has read the message.
    """

    room = ReferenceField(Room, required=True, reverse_delete_rule=CASCADE)
    sender_email = StringField(required=True)
    receiver_email = StringField(required=True)
    text = EncryptedStringField(required=True)
    timestamp = DateTimeField(default=lambda: datetime.now(timezone.utc))
    is_read = BooleanField(default=False)

    meta = {
        "collection": "messages",
        "db_alias": "chat_test"
    }

    @property
    def room_name(self):
        return self.room.name if self.room else None

    def clean(self):
        """
        Validates the integrity and constraints of the `Message` document.

        Rules:
            - The message must be linked to a valid, persisted `Room`.
            - Both sender and receiver must be participants of the room.
            - Sender and receiver must not be the same user.
            - The room must have exactly 2 participants (private chat).
            - The message text cannot be empty.
            - The text must not contain forbidden words (from FORBIDDEN_WORDS_SET).
            - The text must not contain excessive character spam (e.g., 10+ repeated consonants).
            - The message text is sanitized before saving.

        Raises:
            ValidationError: If any of the above constraints are violated.
        """
        try:
            if not self.room or not self.room.id:
                raise ValidationError("Message must belong to a persisted room.")

            if self.sender_email not in self.room.participants:
                raise ValidationError("Sender must be a participant of the room.")

            if self.receiver_email not in self.room.participants:
                raise ValidationError("Receiver must be a participant of the room.")

            if self.sender_email == self.receiver_email:
                raise ValidationError("Sender and receiver cannot be the same.")

            if len(self.room.participants) != 2:
                raise ValidationError("Private room must have exactly 2 participants.")

            if not self.text.strip():
                raise ValidationError("Message text cannot be empty.")

            if len(self.text) < MIN_MESSAGE_LENGTH or len(self.text) > MAX_MESSAGE_LENGTH:
                raise ValidationError(
                    f"Message length must be between {MIN_MESSAGE_LENGTH} and {MAX_MESSAGE_LENGTH} characters."
                )

            lowered = self.text.lower()
            forbidden_pattern = r'\b(?:' + '|'.join(re.escape(word) for word in FORBIDDEN_WORDS_SET) + r')\b'
            if re.search(forbidden_pattern, lowered):
                raise ValidationError("Message contains forbidden content.")

            if re.search(r"([^aeiou\s])\1{10,}", self.text, re.IGNORECASE):
                raise ValidationError("Message looks like spam.")

            self.text = sanitize_message(self.text)

        except ValidationError as ve:
            logger.warning("[MESSAGE_VALIDATION] Failed validation | sender=%s receiver=%s room=%s error=%s",
                           self.sender_email, self.receiver_email,
                           getattr(self.room, 'name', 'UNKNOWN'), ve)
            sentry_sdk.capture_exception(ve)
            raise ve

    @log_and_capture("message", ValidationError)
    def save(self, *args, **kwargs):
        self.timestamp = datetime.now(timezone.utc)
        return super().save(*args, **kwargs)

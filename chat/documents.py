from mongoengine import Document, StringField, ListField, ReferenceField, DateTimeField, BooleanField, ValidationError
from datetime import datetime, timezone
import re
from core.settings import FORBIDDEN_WORDS


class Room(Document):
    """
    Represents a chat room in MongoDB.

    Attributes:
        name (str): Unique name of the room, 3–50 characters, only letters, numbers, dash, underscore.
        participants (List[User]): List of users participating in this room.
        created_at (datetime): Time when the room was created (UTC).
        updated_at (datetime): Time when the room was last updated (UTC).
    """

    name = StringField(
        required=True,
        min_length=3,
        max_length=50,
        regex=r'^[a-zA-Z0-9_-]+$',
        unique=True
    )
    participants = ListField(ReferenceField('UserDocument'))
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    def clean(self):
        """
        Validate room data before saving:
        - Remove duplicate participants.
        - Limit participants to 50.
        - Ensure room name matches allowed pattern.
        """
        self.participants = list(set(self.participants))

        if len(self.participants) > 50:
            raise ValidationError("Room cannot have more than 50 participants")

        if not re.match(r'^[a-zA-Z0-9_-]+$', self.name):
            raise ValidationError("Room name can only contain letters, numbers, dashes, and underscores")

    def save(self, *args, **kwargs):
        """
        Update the 'updated_at' timestamp before saving.
        """
        self.updated_at = datetime.now(timezone.utc)
        return super().save(*args, **kwargs)


class Message(Document):
    """
    Represents a single chat message in a room.

    Attributes:
        room (Room): Reference to the room where the message belongs.
        sender (User): Reference to the user who sent the message.
        text (str): Message content, 1–1000 characters.
        timestamp (datetime): Time when the message was created (UTC).
        is_read (bool): Indicates whether the message has been read.
    """

    room = ReferenceField(Room, required=True)
    sender = ReferenceField('UserDocument', required=True)
    text = StringField(required=True, min_length=1, max_length=1000)
    timestamp = DateTimeField(default=lambda: datetime.now(timezone.utc))
    is_read = BooleanField(default=False)

    def clean(self):
        """
        Validate message data before saving:
        - Ensure sender is part of the room.
        - Ensure message doesn't contain forbidden words.
        - Block messages that appear spammy (repeated characters).
        """
        if self.sender not in self.room.participants:
            raise ValidationError("Sender must be a participant of the room.")

        lowered = self.text.lower()
        if any(word in lowered for word in FORBIDDEN_WORDS):
            raise ValidationError("Message contains forbidden content.")

        if re.search(r"(.)\1{5,}", self.text):
            raise ValidationError("Message looks like spam.")

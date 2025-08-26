import os
from mongoengine import CASCADE
from mongoengine import Document, StringField, ListField, ReferenceField, DateTimeField, BooleanField, ValidationError
from datetime import datetime, timezone
import re
from core.settings.constants import FORBIDDEN_WORDS_SET

MAX_PARTICIPANTS = int(os.getenv("MAX_PARTICIPANTS", 50))
MIN_MESSAGE_LENGTH = int(os.getenv("MIN_MESSAGE_LENGTH", 1))
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 1000))


class Room(Document):
    """
    Represents a chat room in MongoDB.

    Attributes:
        name (str): Unique name of the room, 3–50 characters, only letters, numbers, dash, underscore.
        participants (List[UserDocument]): List of users participating in this room.
        created_at (datetime): Time when the room was created (UTC).
        updated_at (datetime): Time when the room was last updated (UTC).
    """

    NAME_REGEX = r'^[a-zA-Z0-9_-]+$'

    name = StringField(
        required=True,
        min_length=3,
        max_length=50,
        regex=NAME_REGEX,
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
        seen = set()
        deduped_participants = []
        for user in self.participants:
            if user.id not in seen:
                deduped_participants.append(user)
                seen.add(user.id)
        self.participants = deduped_participants

        if len(self.participants) > MAX_PARTICIPANTS:
            raise ValidationError("Room cannot have more than 50 participants")

    def save(self, *args, **kwargs):
        """
        Update the 'updated_at' timestamp before saving.
        """
        self.updated_at = datetime.now(timezone.utc)
        self.clean()
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

    room = ReferenceField(Room, required=True, reverse_delete_rule=CASCADE)
    sender = ReferenceField('UserDocument', required=True)
    text = StringField(required=True, min_length=MIN_MESSAGE_LENGTH, max_length=MAX_MESSAGE_LENGTH)
    timestamp = DateTimeField(default=lambda: datetime.now(timezone.utc))
    is_read = BooleanField(default=False)

    def clean(self):
        """
        Validate message data before saving:
        - Ensure the message has a valid room.
        - Ensure sender is persisted and part of the room.
        - Ensure message doesn't contain forbidden words.
        - Block messages that appear spammy (repeated characters).
        """
        if not self.room:
            raise ValidationError("Message must belong to a valid room.")

        if not self.sender or not self.sender.id:
            raise ValidationError("Sender must be a persisted user.")

        participant_ids = {u.id for u in self.room.participants}
        if self.sender.id not in participant_ids:
            raise ValidationError("Sender must be a participant of the room.")

        if not self.text:
            raise ValidationError("Message text cannot be empty.")

        lowered = self.text.lower()
        forbidden_pattern = r'\b(?:' + '|'.join(re.escape(word) for word in FORBIDDEN_WORDS_SET) + r')\b'
        if re.search(forbidden_pattern, lowered):
            raise ValidationError("Message contains forbidden content.")

        if re.search(r"([^aeiou\s])\1{10,}", self.text, re.IGNORECASE):
            raise ValidationError("Message looks like spam.")

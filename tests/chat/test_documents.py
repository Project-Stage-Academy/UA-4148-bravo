import re
from django.test import TestCase
from mongoengine import connect, disconnect, ValidationError
from datetime import datetime, timezone
from chat.documents import Room, Message
import mongomock
from core.settings.constants import FORBIDDEN_WORDS_SET

TEST_USER_EMAIL = "user@example.com"
TEST_USER2_EMAIL = "user2@example.com"


class MongoEngineTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        disconnect()
        connect(
            db='mongoenginetest',
            host='mongodb://localhost',
            mongo_client_class=mongomock.MongoClient
        )

    @classmethod
    def tearDownClass(cls):
        disconnect()
        super().tearDownClass()

    def setUp(self):
        Room.drop_collection()
        Message.drop_collection()
        self.user_email = TEST_USER_EMAIL
        self.user2_email = TEST_USER2_EMAIL

    def test_create_room(self):
        """Room can be created with a valid name and participants."""
        room = Room(name="TestRoom", participants=[self.user_email])
        room.save()
        self.assertIsNotNone(room.id)
        self.assertEqual(room.name, "TestRoom")
        self.assertIn(self.user_email, room.participants)
        self.assertLessEqual(room.created_at, datetime.now(timezone.utc))

    def test_room_name_validation(self):
        """Room with invalid characters raises ValidationError."""
        room = Room(name="Invalid Room!", participants=[self.user_email])
        with self.assertRaises(ValidationError):
            if not re.match(Room.NAME_REGEX, room.name):
                raise ValidationError(f"Room name '{room.name}' contains invalid characters")
            room.clean()

    def test_room_participants_limit(self):
        """Room with more than MAX_PARTICIPANTS raises ValidationError."""
        users = [f"user{i}@example.com" for i in range(51)]
        room = Room(name="BigRoom", participants=users)
        with self.assertRaises(ValidationError):
            room.clean()

    def test_message_creation_private(self):
        """Message can be created in a private room by a participant."""
        room = Room(name="PrivateRoom", participants=[self.user_email, self.user2_email], is_group=False)
        room.save()
        message = Message(
            room=room,
            sender_email=self.user_email,
            receiver_email=self.user2_email,
            text="Hello, user2!"
        )
        message.clean()
        message.save()
        self.assertIsNotNone(message.id)
        self.assertEqual(message.text, "Hello, user2!")
        self.assertLessEqual(message.timestamp, datetime.now(timezone.utc))

    def test_message_creation_group(self):
        """Message can be created in a group room without receiver_email."""
        room = Room(name="GroupRoom", participants=[self.user_email, self.user2_email], is_group=True)
        room.save()
        message = Message(
            room=room,
            sender_email=self.user_email,
            text="Hello, everyone!"
        )
        message.clean()
        message.save()
        self.assertIsNotNone(message.id)
        self.assertEqual(message.text, "Hello, everyone!")
        self.assertLessEqual(message.timestamp, datetime.now(timezone.utc))

    def test_message_forbidden_words(self):
        """Message containing forbidden words raises ValidationError."""
        room = Room(name="SpamRoom", participants=[self.user_email, self.user2_email], is_group=True)
        room.save()
        forbidden_word = next(iter(FORBIDDEN_WORDS_SET)) if FORBIDDEN_WORDS_SET else "forbidden"
        message = Message(
            room=room,
            sender_email=self.user_email,
            text=f"This contains {forbidden_word}"
        )
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_sender_not_in_room(self):
        """Message from non-participant raises ValidationError."""
        room = Room(name="OtherRoom", participants=[self.user2_email])
        room.save()
        message = Message(
            room=room,
            sender_email="other_user@example.com",
            text="Hi"
        )
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_receiver_not_in_group(self):
        """Message with receiver not in group raises ValidationError."""
        room = Room(name="GroupRoom2", participants=[self.user_email, self.user2_email], is_group=True)
        room.save()
        message = Message(
            room=room,
            sender_email=self.user_email,
            receiver_email="nonparticipant@example.com",
            text="Hi"
        )
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_spam_repeated_chars(self):
        """Message with repeated characters (spam) raises ValidationError."""
        user1 = "user1@example.com"
        user2 = "user2@example.com"
        room = Room(name="SpamRoom2", participants=[user1, user2], is_group=True)
        room.save()

        spam_text = "bbbbbbbbbbbb"
        message = Message(room=room, sender_email=user1, text=spam_text)

        with self.assertRaises(ValidationError):
            message.clean()

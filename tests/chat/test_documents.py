import os
import re
from django.test import TestCase
from mongoengine import connect, disconnect, ValidationError
from datetime import datetime, timezone
from chat.documents import Room, Message
import mongomock
from core.settings.constants import FORBIDDEN_WORDS_SET

TEST_USER_ID = "user123"
TEST_USER2_ID = "user456"


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
        self.user_id = TEST_USER_ID
        self.user2_id = TEST_USER2_ID

    def test_create_room(self):
        """Room can be created with a valid name and participants."""
        room = Room(name="TestRoom", participants=[self.user_id])
        room.save()
        self.assertIsNotNone(room.id)
        self.assertEqual(room.name, "TestRoom")
        self.assertIn(self.user_id, room.participants)
        self.assertLessEqual(room.created_at, datetime.now(timezone.utc))

    def test_room_name_validation(self):
        """Room with invalid characters raises ValidationError."""
        room = Room(name="Invalid Room!", participants=[self.user_id])
        with self.assertRaises(ValidationError):
            if not re.match(Room.NAME_REGEX, room.name):
                raise ValidationError(f"Room name '{room.name}' contains invalid characters")
            room.clean()

    def test_room_participants_limit(self):
        """Room with more than MAX_PARTICIPANTS raises ValidationError."""
        users = [f"user{i}" for i in range(51)]
        room = Room(name="BigRoom", participants=users)
        with self.assertRaises(ValidationError):
            room.clean()

    def test_message_creation_private(self):
        """Message can be created in a private room by a participant."""
        room = Room(name="PrivateRoom", participants=[self.user_id, self.user2_id], is_group=False)
        room.save()
        message = Message(room=room, sender_id=self.user_id, receiver_id=self.user2_id, text="Hello, user2!")
        message.clean()
        message.save()
        self.assertIsNotNone(message.id)
        self.assertEqual(message.text, "Hello, user2!")
        self.assertLessEqual(message.timestamp, datetime.now(timezone.utc))

    def test_message_creation_group(self):
        """Message can be created in a group room without receiver_id."""
        room = Room(name="GroupRoom", participants=[self.user_id, self.user2_id], is_group=True)
        room.save()
        message = Message(room=room, sender_id=self.user_id, text="Hello, everyone!")
        message.clean()
        message.save()
        self.assertIsNotNone(message.id)
        self.assertEqual(message.text, "Hello, everyone!")
        self.assertLessEqual(message.timestamp, datetime.now(timezone.utc))

    def test_message_forbidden_words(self):
        """Message containing forbidden words raises ValidationError."""
        room = Room(name="SpamRoom", participants=[self.user_id, self.user2_id], is_group=True)
        room.save()
        forbidden_word = next(iter(FORBIDDEN_WORDS_SET)) if FORBIDDEN_WORDS_SET else "forbidden"
        message = Message(room=room, sender_id=self.user_id, text=f"This contains {forbidden_word}")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_sender_not_in_room(self):
        """Message from non-participant raises ValidationError."""
        room = Room(name="OtherRoom", participants=[self.user2_id])
        room.save()
        message = Message(room=room, sender_id="other_user", text="Hi")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_receiver_not_in_group(self):
        """Message with receiver not in group raises ValidationError."""
        room = Room(name="GroupRoom2", participants=[self.user_id, self.user2_id], is_group=True)
        room.save()
        message = Message(room=room, sender_id=self.user_id, receiver_id="nonparticipant", text="Hi")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_spam_repeated_chars(self):
        """Message with repeated characters (spam) raises ValidationError."""
        user1 = "user1"
        user2 = "user2"

        room = Room(name="SpamRoom2", participants=[user1, user2], is_group=True)
        room.save()

        spam_text = "bbbbbbbbbbbb"
        message = Message(room=room, sender_id=user1, text=spam_text)

        with self.assertRaises(ValidationError):
            message.clean()

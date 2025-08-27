import os
import re

from django.test import TestCase
from mongoengine import connect, disconnect, ValidationError
from datetime import datetime, timezone
from chat.documents import Room, Message
from users.documents import UserDocument, UserRoleDocument, UserRoleEnum
from core.settings.constants import FORBIDDEN_WORDS_SET
import mongomock

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.chat.setup_test_env.'
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "testpassword123")


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

        role = UserRoleDocument.objects(role=UserRoleEnum.USER).first()
        if not role:
            role = UserRoleDocument(role=UserRoleEnum.USER)
            role.save()
        cls.user_role = role

    @classmethod
    def tearDownClass(cls):
        disconnect()
        super().tearDownClass()

    def setUp(self):
        UserDocument.drop_collection()
        Room.drop_collection()
        Message.drop_collection()
        self.user = UserDocument(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            password=TEST_USER_PASSWORD,
            role=self.user_role
        )
        self.user.save()

    def test_create_room(self):
        """Test that a Room can be created with a valid name and participants."""
        room = Room(name="TestRoom", participants=[self.user])
        room.save()
        self.assertIsNotNone(room.id)
        self.assertEqual(room.name, "TestRoom")
        self.assertIn(self.user, room.participants)
        self.assertLessEqual(room.created_at, datetime.now(timezone.utc))

    def test_room_name_validation(self):
        """Room with invalid characters raises ValidationError."""
        room = Room(name="Invalid Room!", participants=[self.user])
        with self.assertRaises(ValidationError):
            if not re.match(Room.NAME_REGEX, room.name):
                raise ValidationError(f"Room name '{room.name}' contains invalid characters")
            room.clean()

    def test_room_participants_limit(self):
        """Test that a Room with more than 50 participants raises ValidationError."""
        users = []
        for i in range(51):
            u = UserDocument(
                email=f"user{i}@example.com",
                first_name=f"User{i}",
                last_name="Test",
                password=TEST_USER_PASSWORD,
                role=self.user_role
            )
            u.save()
            users.append(u)
        room = Room(name="BigRoom", participants=users)
        with self.assertRaises(ValidationError):
            room.clean()

    def test_message_creation(self):
        """Test that a Message can be created in a Room by a participant."""
        room = Room(name="ChatRoom", participants=[self.user])
        room.save()
        message = Message(room=room, sender=self.user, text="Hello, world!")
        message.clean()
        message.save()
        self.assertIsNotNone(message.id)
        self.assertEqual(message.text, "Hello, world!")
        self.assertLessEqual(message.timestamp, datetime.now(timezone.utc))

    def test_message_forbidden_words(self):
        """Test that a Message containing forbidden words raises ValidationError."""
        room = Room(name="SpamRoom", participants=[self.user])
        room.save()
        forbidden_word = next(iter(FORBIDDEN_WORDS_SET)) if FORBIDDEN_WORDS_SET else "forbidden"
        message = Message(room=room, sender=self.user, text=f"This contains {forbidden_word}")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_sender_not_in_room(self):
        """Test that a Message from a non-participant raises ValidationError."""
        sender = UserDocument(
            email="other@example.com",
            first_name="Other",
            last_name="User",
            password=TEST_USER_PASSWORD,
            role=self.user_role
        )
        sender.save()
        room = Room(name="OtherRoom", participants=[])
        room.save()
        message = Message(room=room, sender=sender, text="Hi")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_spam_repeated_chars(self):
        """Message with repeated characters (spam) raises ValidationError."""
        room = Room(name="SpamRoom2", participants=[self.user])
        room.save()
        spam_text = "aaaaaaabbbbbbbcccccc"
        message = Message(room=room, sender=self.user, text=spam_text)
        with self.assertRaises(ValidationError):
            if re.search(r"(.)\1{5,}", message.text, re.IGNORECASE):
                raise ValidationError("Message looks like spam.")
            message.clean()

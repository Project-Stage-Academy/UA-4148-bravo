from django.test import TestCase
from mongoengine import connect, disconnect, ValidationError
from datetime import datetime, timezone
from chat.models import Room, Message

class MongoEngineTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        connect('mongoenginetest', host='mongomock://localhost')

    @classmethod
    def tearDownClass(cls):
        disconnect()
        super().tearDownClass()

    def setUp(self):
        class User:
            id = 1
        self.user = User()

    def test_create_room(self):
        room = Room(name="TestRoom", participants=[self.user])
        room.save()
        self.assertIsNotNone(room.id)
        self.assertEqual(room.name, "TestRoom")
        self.assertIn(self.user, room.participants)
        self.assertLessEqual(room.created_at, datetime.now(timezone.utc))

    def test_room_name_validation(self):
        room = Room(name="Invalid Room!", participants=[self.user])
        with self.assertRaises(ValidationError):
            room.clean()

    def test_room_participants_limit(self):
        users = [f"user{i}" for i in range(51)]
        room = Room(name="BigRoom", participants=users)
        with self.assertRaises(ValidationError):
            room.clean()

    def test_message_creation(self):
        room = Room(name="ChatRoom", participants=[self.user])
        room.save()
        message = Message(room=room, sender=self.user, text="Hello, world!")
        message.clean()
        message.save()
        self.assertIsNotNone(message.id)
        self.assertEqual(message.text, "Hello, world!")
        self.assertLessEqual(message.timestamp, datetime.now(timezone.utc))

    def test_message_forbidden_words(self):
        room = Room(name="SpamRoom", participants=[self.user])
        room.save()
        message = Message(room=room, sender=self.user, text="This is free money!")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_sender_not_in_room(self):
        class FakeUser:
            id = 999
        sender = FakeUser()
        room = Room(name="OtherRoom", participants=[])
        room.save()
        message = Message(room=room, sender=sender, text="Hi")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_spam_repeated_chars(self):
        room = Room(name="SpamRoom2", participants=[self.user])
        room.save()
        spam_text = "aaaaaaabbbbbbbcccccc"
        message = Message(room=room, sender=self.user, text=spam_text)
        with self.assertRaises(ValidationError):
            message.clean()

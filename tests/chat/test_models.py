from django.test import TestCase
from mongoengine import connect, disconnect, ValidationError
from datetime import datetime, timezone
from chat.documents import Room, Message
from users.documents import UserDocument, UserRoleDocument, UserRoleEnum
from core.settings import FORBIDDEN_WORDS


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
        role = UserRoleDocument(role=UserRoleEnum.USER)
        role.save()
        self.user = UserDocument(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            password="secret",
            role=role
        )
        self.user.save()

    def test_create_room(self):
        """
        Test that a Room can be created with a valid name and participants.
        Verifies that the room ID is set, the name is correct, the user is in participants,
        and the creation timestamp is not in the future.
        """
        room = Room(name="TestRoom", participants=[self.user])
        room.save()
        self.assertIsNotNone(room.id)
        self.assertEqual(room.name, "TestRoom")
        self.assertIn(self.user, room.participants)
        self.assertLessEqual(room.created_at, datetime.now(timezone.utc))

    def test_room_name_validation(self):
        """
        Test that creating a Room with invalid characters in the name
        raises a ValidationError.
        """
        room = Room(name="Invalid Room!", participants=[self.user])
        with self.assertRaises(ValidationError):
            room.clean()

    def test_room_participants_limit(self):
        """
        Test that a Room with more than 50 participants
        raises a ValidationError.
        """
        role = UserRoleDocument.objects(role=UserRoleEnum.USER).first()
        users = []
        for i in range(51):
            u = UserDocument(
                email=f"user{i}@example.com",
                first_name=f"User{i}",
                last_name="Test",
                password="pass",
                role=role
            )
            u.save()
            users.append(u)
        room = Room(name="BigRoom", participants=users)
        with self.assertRaises(ValidationError):
            room.clean()

    def test_message_creation(self):
        """
        Test that a Message can be created in a Room by a participant.
        Verifies that the message ID is set, the text is correct,
        and the timestamp is not in the future.
        """
        room = Room(name="ChatRoom", participants=[self.user])
        room.save()
        message = Message(room=room, sender=self.user, text="Hello, world!")
        message.clean()
        message.save()
        self.assertIsNotNone(message.id)
        self.assertEqual(message.text, "Hello, world!")
        self.assertLessEqual(message.timestamp, datetime.now(timezone.utc))

    def test_message_forbidden_words(self):
        """
        Test that a Message containing forbidden words
        raises a ValidationError.
        """
        room = Room(name="SpamRoom", participants=[self.user])
        room.save()
        forbidden_word = FORBIDDEN_WORDS[0] if FORBIDDEN_WORDS else "forbidden"
        message = Message(room=room, sender=self.user, text=f"This contains {forbidden_word}")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_sender_not_in_room(self):
        """
        Test that a Message sent by a user who is not a participant
        of the Room raises a ValidationError.
        """
        role = UserRoleDocument.objects(role=UserRoleEnum.USER).first()
        sender = UserDocument(
            email="other@example.com",
            first_name="Other",
            last_name="User",
            password="pass",
            role=role
        )
        sender.save()
        room = Room(name="OtherRoom", participants=[])
        room.save()
        message = Message(room=room, sender=sender, text="Hi")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_message_spam_repeated_chars(self):
        """
        Test that a Message containing repeated characters (spammy content)
        raises a ValidationError.
        """
        room = Room(name="SpamRoom2", participants=[self.user])
        room.save()
        spam_text = "aaaaaaabbbbbbbcccccc"
        message = Message(room=room, sender=self.user, text=spam_text)
        with self.assertRaises(ValidationError):
            message.clean()

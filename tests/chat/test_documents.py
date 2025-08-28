import mongomock
from django.test import TestCase
from mongoengine import connect, disconnect, ValidationError
from chat.documents import Room, Message
from core.settings.constants import FORBIDDEN_WORDS_SET

TEST_USER_EMAIL = "user@example.com"
TEST_USER2_EMAIL = "user2@example.com"
TEST_USER3_EMAIL = "user3@example.com"


class ChatDocumentsTestCase(TestCase):
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
        self.user1 = TEST_USER_EMAIL
        self.user2 = TEST_USER2_EMAIL
        self.user3 = TEST_USER3_EMAIL

    def test_room_creation_and_limits(self):
        """Room creation and participant limits."""
        room = Room(name="RoomTest", participants=[self.user1, self.user2])
        room.save()
        self.assertIsNotNone(room.id)
        self.assertEqual(len(room.participants), 2)
        users = [f"user{i}@example.com" for i in range(51)]
        room = Room(name="BigRoom", participants=users)
        with self.assertRaises(ValidationError):
            room.clean()

    def _create_room(self, is_group=True, participants=None):
        if participants is None:
            participants = [self.user1, self.user2]
        room = Room(name=f"Room_{is_group}", participants=participants, is_group=is_group)
        room.save()
        return room

    def test_private_message_valid(self):
        """Private message with exactly 2 participants and valid receiver."""
        room = self._create_room(is_group=False, participants=[self.user1, self.user2])
        message = Message(room=room, sender_email=self.user1, receiver_email=self.user2, text="Hello!")
        message.clean()
        message.save()
        self.assertIsNotNone(message.id)

    def test_private_message_missing_receiver(self):
        """Private message without receiver raises ValidationError."""
        room = self._create_room(is_group=False, participants=[self.user1, self.user2])
        message = Message(room=room, sender_email=self.user1, text="Hello!")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_private_message_wrong_participant_count(self):
        """Private room must have exactly 2 participants."""
        room = self._create_room(is_group=False, participants=[self.user1, self.user2, self.user3])
        message = Message(room=room, sender_email=self.user1, receiver_email=self.user2, text="Hello!")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_group_message_valid_no_receiver(self):
        """Group message without receiver_email is valid."""
        room = self._create_room(is_group=True)
        message = Message(room=room, sender_email=self.user1, text="Hi everyone!")
        message.clean()
        message.save()
        self.assertIsNotNone(message.id)

    def test_group_message_with_receiver_in_group(self):
        """Group message with receiver_email who is in participants is valid."""
        room = self._create_room(is_group=True)
        message = Message(room=room, sender_email=self.user1, receiver_email=self.user2, text="Hi!")
        message.clean()
        message.save()
        self.assertIsNotNone(message.id)

    def test_group_message_with_receiver_not_in_group(self):
        """Group message with receiver_email not in participants raises ValidationError."""
        room = self._create_room(is_group=True)
        message = Message(room=room, sender_email=self.user1, receiver_email=self.user3, text="Hi!")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_sender_not_in_room(self):
        """Message from non-participant raises ValidationError."""
        room = self._create_room(is_group=True)
        message = Message(room=room, sender_email=self.user3, text="Hi!")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_empty_text_message(self):
        """Message with empty text raises ValidationError."""
        room = self._create_room()
        message = Message(room=room, sender_email=self.user1, text="   ")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_forbidden_words(self):
        """Message with forbidden words raises ValidationError."""
        room = self._create_room()
        forbidden_word = next(iter(FORBIDDEN_WORDS_SET)) if FORBIDDEN_WORDS_SET else "badword"
        message = Message(room=room, sender_email=self.user1, text=f"This is {forbidden_word}")
        with self.assertRaises(ValidationError):
            message.clean()

    def test_spam_repeated_chars(self):
        """Message with repeated characters (spam) raises ValidationError."""
        room = self._create_room()
        message = Message(room=room, sender_email=self.user1, text="bbbbbbbbbbbb")
        with self.assertRaises(ValidationError):
            message.clean()

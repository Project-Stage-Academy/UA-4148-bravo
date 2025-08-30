import mongomock
from django.test import TestCase
from mongoengine import connect, disconnect, ValidationError
from chat.documents import Room, Message, FORBIDDEN_WORDS_SET


TEST_USER_EMAIL = "user@example.com"
TEST_USER2_EMAIL = "user2@example.com"
TEST_USER3_EMAIL = "user3@example.com"


class ChatDocumentsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        disconnect()
        connect(
            db="mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
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

    def _create_room(self, participants=None):
        if participants is None:
            participants = [self.user1, self.user2]
        room = Room(name="TestRoom", participants=participants)
        room.save()
        return room

    def test_room_creation_and_limits(self):
        """Room creation with exactly 2 participants works, more raises ValidationError."""
        room = Room(name="RoomTest", participants=[self.user1, self.user2])
        room.save()
        self.assertIsNotNone(room.id)
        self.assertEqual(len(room.participants), 2)

        room = Room(name="TooMany", participants=[self.user1, self.user2, self.user3])
        with self.assertRaises(ValidationError):
            room.save()

    def test_private_message_valid(self):
        """Private message with exactly 2 participants and valid receiver."""
        room = self._create_room()
        message = Message(
            room=room, sender_email=self.user1, receiver_email=self.user2, text="Hello!"
        )
        message.save()
        self.assertIsNotNone(message.id)

    def test_private_message_missing_receiver(self):
        """Private message without receiver raises ValidationError."""
        room = self._create_room()
        message = Message(room=room, sender_email=self.user1, text="Hello!")
        with self.assertRaises(ValidationError):
            message.save()

    def test_private_message_wrong_participant_count(self):
        """Room with wrong participants count makes message invalid."""
        room = self._create_room(participants=[self.user1, self.user2, self.user3])
        message = Message(
            room=room, sender_email=self.user1, receiver_email=self.user2, text="Hello!"
        )
        with self.assertRaises(ValidationError):
            message.save()

    def test_sender_not_in_room(self):
        """Message from non-participant raises ValidationError."""
        room = self._create_room()
        message = Message(
            room=room, sender_email=self.user3, receiver_email=self.user1, text="Hi!"
        )
        with self.assertRaises(ValidationError):
            message.save()

    def test_receiver_not_in_room(self):
        """Receiver not in room raises ValidationError."""
        room = self._create_room()
        message = Message(
            room=room, sender_email=self.user1, receiver_email=self.user3, text="Hi!"
        )
        with self.assertRaises(ValidationError):
            message.save()

    def test_sender_equals_receiver(self):
        """Sender == receiver is invalid."""
        room = self._create_room()
        message = Message(
            room=room, sender_email=self.user1, receiver_email=self.user1, text="Bad"
        )
        with self.assertRaises(ValidationError):
            message.save()

    def test_empty_text_message(self):
        """Message with empty text raises ValidationError."""
        room = self._create_room()
        message = Message(room=room, sender_email=self.user1, receiver_email=self.user2, text="   ")
        with self.assertRaises(ValidationError):
            message.save()

    def test_forbidden_words(self):
        """Message with forbidden words raises ValidationError."""
        room = self._create_room()
        forbidden_word = next(iter(FORBIDDEN_WORDS_SET)) if FORBIDDEN_WORDS_SET else "badword"
        message = Message(
            room=room,
            sender_email=self.user1,
            receiver_email=self.user2,
            text=f"This is {forbidden_word}",
        )
        with self.assertRaises(ValidationError):
            message.save()

    def test_spam_repeated_chars(self):
        """Message with repeated characters (spam) raises ValidationError."""
        room = self._create_room()
        message = Message(
            room=room,
            sender_email=self.user1,
            receiver_email=self.user2,
            text="bbbbbbbbbbbb",
        )
        with self.assertRaises(ValidationError):
            message.save()

    def test_room_name_html_escape(self):
        """Room name should be HTML-escaped."""
        raw_name = '<script>alert("XSS")</script>'
        room = Room(name=raw_name, participants=[self.user1, self.user2])
        room.save()
        self.assertEqual(room.name, '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;')

    def test_message_text_html_escape(self):
        """Message text should be HTML-escaped."""
        room = self._create_room()
        raw_text = '<b>Hello</b> & welcome!'
        message = Message(
            room=room, sender_email=self.user1, receiver_email=self.user2, text=raw_text
        )
        message.save()
        self.assertEqual(message.text, '&lt;b&gt;Hello&lt;/b&gt; &amp; welcome!')

    def test_room_name_strip_and_escape(self):
        """Room name with spaces is stripped and escaped."""
        raw_name = '  <Room>  '
        room = Room(name=raw_name, participants=[self.user1, self.user2])
        room.save()
        self.assertEqual(room.name, '&lt;Room&gt;')

    def test_message_text_strip_and_escape(self):
        """Message text with spaces is stripped and escaped."""
        room = self._create_room()
        raw_text = '   <Hello>   '
        message = Message(
            room=room, sender_email=self.user1, receiver_email=self.user2, text=raw_text
        )
        message.save()
        self.assertEqual(message.text, '&lt;Hello&gt;')

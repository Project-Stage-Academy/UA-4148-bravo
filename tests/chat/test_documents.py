from mongoengine import ValidationError
from chat.documents import Room, Message, FORBIDDEN_WORDS_SET
from tests.chat.test_create_users import BaseChatTestCase, TEST_EMAIL_1, TEST_EMAIL_2, TEST_EMAIL_3


class ChatDocumentsTestCase(BaseChatTestCase):

    def setUp(self):
        Room.drop_collection()
        Message.drop_collection()

    def _create_room(self, participants=None):
        participants = participants or [TEST_EMAIL_1, TEST_EMAIL_2]
        room = Room(name="TestRoom", participants=participants)
        room.save()
        return room

    def test_room_creation_and_limits(self):
        """Room creation with exactly 2 participants works, more raises ValidationError."""
        room = Room(name="RoomTest", participants=[TEST_EMAIL_1, TEST_EMAIL_2])
        room.save()
        self.assertIsNotNone(room.id)
        self.assertEqual(len(room.participants), 2)

        room = Room(name="TooMany", participants=[TEST_EMAIL_1, TEST_EMAIL_2, TEST_EMAIL_3])
        with self.assertRaises(ValidationError):
            room.save()

    def test_private_message_valid(self):
        """Private message with exactly 2 participants and valid receiver."""
        room = self._create_room()
        message = Message(
            room=room, sender_email=TEST_EMAIL_1, receiver_email=TEST_EMAIL_2, text="Hello!"
        )
        message.save()
        self.assertIsNotNone(message.id)

    def test_private_message_missing_receiver(self):
        """Private message without receiver raises ValidationError."""
        room = self._create_room()
        message = Message(room=room, sender_email=TEST_EMAIL_1, text="Hello!")
        with self.assertRaises(ValidationError):
            message.save()

    def test_private_message_wrong_participant_count(self):
        """Room with wrong participants count makes message invalid."""
        room = Room(name="InvalidRoom", participants=[TEST_EMAIL_1, TEST_EMAIL_2, TEST_EMAIL_3])
        room.id = "dummy_id"

        message = Message(
            room=room, sender_email=TEST_EMAIL_1, receiver_email=TEST_EMAIL_2, text="Hello!"
        )

        with self.assertRaises(ValidationError):
            message.save()

    def test_sender_not_in_room(self):
        """Message from non-participant raises ValidationError."""
        room = self._create_room()
        message = Message(
            room=room, sender_email=TEST_EMAIL_3, receiver_email=TEST_EMAIL_1, text="Hi!"
        )
        with self.assertRaises(ValidationError):
            message.save()

    def test_receiver_not_in_room(self):
        """Receiver not in room raises ValidationError."""
        room = self._create_room()
        message = Message(
            room=room, sender_email=TEST_EMAIL_1, receiver_email=TEST_EMAIL_3, text="Hi!"
        )
        with self.assertRaises(ValidationError):
            message.save()

    def test_sender_equals_receiver(self):
        """Sender == receiver is invalid."""
        room = self._create_room()
        message = Message(
            room=room, sender_email=TEST_EMAIL_1, receiver_email=TEST_EMAIL_1, text="Bad"
        )
        with self.assertRaises(ValidationError):
            message.save()

    def test_empty_text_message(self):
        """Message with empty text raises ValidationError."""
        room = self._create_room()
        message = Message(room=room, sender_email=TEST_EMAIL_1, receiver_email=TEST_EMAIL_2, text=" ")
        with self.assertRaises(ValidationError):
            message.save()

    def test_forbidden_words(self):
        """Message with forbidden words raises ValidationError."""
        room = self._create_room()
        forbidden_word = next(iter(FORBIDDEN_WORDS_SET)) if FORBIDDEN_WORDS_SET else "badword"
        message = Message(
            room=room,
            sender_email=TEST_EMAIL_1,
            receiver_email=TEST_EMAIL_2,
            text=f"This is {forbidden_word}",
        )
        with self.assertRaises(ValidationError):
            message.save()

    def test_spam_repeated_chars(self):
        """Message with repeated characters (spam) raises ValidationError."""
        room = self._create_room()
        message = Message(
            room=room,
            sender_email=TEST_EMAIL_1,
            receiver_email=TEST_EMAIL_2,
            text="bbbbbbbbbbbb",
        )
        with self.assertRaises(ValidationError):
            message.save()

    def test_room_name_html_escape(self):
        """Room name should be stripped of dangerous tags."""
        raw_name = '<Room123>'
        room = Room(name=raw_name, participants=[TEST_EMAIL_1, TEST_EMAIL_2])
        room.save()
        self.assertEqual(room.name, 'Room123')

    def test_room_name_strip_and_escape(self):
        """Room name with spaces is stripped and sanitized."""
        raw_name = '  Room_45  '
        room = Room(name=raw_name, participants=[TEST_EMAIL_1, TEST_EMAIL_2])
        room.save()
        self.assertEqual(room.name, 'Room_45')

    def test_message_text_html_escape(self):
        """Message text should be sanitized and HTML-escaped."""
        room = self._create_room()
        raw_text = '<b>Hello</b> & welcome!'
        message = Message(
            room=room, sender_email=TEST_EMAIL_1, receiver_email=TEST_EMAIL_2, text=raw_text
        )
        message.save()

        expected = '<b>Hello</b> &amp; welcome!'
        self.assertEqual(message.text, expected)

    def test_message_text_strip_and_escape(self):
        """Message text with spaces is stripped and sanitized."""
        room = self._create_room()
        raw_text = '   Hello World   '
        message = Message(
            room=room, sender_email=TEST_EMAIL_1, receiver_email=TEST_EMAIL_2, text=raw_text
        )
        message.save()
        self.assertEqual(message.text, 'Hello World')
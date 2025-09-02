from chat.documents import Room
from chat.serializers import MessageSerializer
from datetime import datetime, timezone
from tests.chat.test_create_users import TEST_EMAIL_1, TEST_EMAIL_2, BaseChatTestCase


class MessageSerializerTest(BaseChatTestCase):

    def setUp(self):
        """Prepare valid base data for tests."""
        Room.drop_collection()
        room = Room(name="room1", participants=[TEST_EMAIL_1, TEST_EMAIL_2])
        room.save()
        self.room = room

        self.valid_data = {
            "room_name": room.name,
            "receiver_email": TEST_EMAIL_2,
            "text": "Hello world!"
        }

    def test_valid_data(self):
        """Serializer accepts valid data and returns expected fields."""
        serializer = MessageSerializer(
            data=self.valid_data,
            context={"sender_email": TEST_EMAIL_1}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save()
        self.assertEqual(message.room, self.room)  # порівнюємо з об'єктом Room
        self.assertEqual(message.receiver_email, self.valid_data["receiver_email"])
        self.assertEqual(message.text, self.valid_data["text"])
        self.assertFalse(message.is_read)
        self.assertIsInstance(message.timestamp, datetime)

    def test_invalid_receiver_email(self):
        """Serializer rejects invalid email format in receiver_email."""
        data = self.valid_data.copy()
        data["receiver_email"] = "not-an-email"
        serializer = MessageSerializer(data=data, context={"sender_email": TEST_EMAIL_1})
        self.assertFalse(serializer.is_valid())
        self.assertIn("receiver_email", serializer.errors)

    def test_too_short_text(self):
        """Serializer rejects text shorter than MIN_MESSAGE_LENGTH."""
        data = self.valid_data.copy()
        data["text"] = ""
        serializer = MessageSerializer(data=data, context={"sender_email": TEST_EMAIL_1})
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors)

    def test_too_long_text(self):
        """Serializer rejects text longer than MAX_MESSAGE_LENGTH."""
        data = self.valid_data.copy()
        data["text"] = "a" * 1001
        serializer = MessageSerializer(data=data, context={"sender_email": TEST_EMAIL_1})
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors)

    def test_is_read_default_false(self):
        """is_read must be False by default if not provided."""
        serializer = MessageSerializer(data=self.valid_data, context={"sender_email": TEST_EMAIL_1})
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        self.assertFalse(message.is_read)

    def test_timestamp_is_auto_generated(self):
        """Serializer automatically generates timestamp on save()."""
        serializer = MessageSerializer(data=self.valid_data, context={"sender_email": TEST_EMAIL_1})
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        self.assertLessEqual(message.timestamp, datetime.now(timezone.utc))

from django.test import TestCase
from chat.serializers import MessageSerializer
from datetime import datetime, timezone


class MessageSerializerTest(TestCase):

    def setUp(self):
        """ Prepare valid base data for tests. """
        self.valid_data = {
            "room": "room1",
            "receiver_email": "user@example.com",
            "text": "Hello world!"
        }

    def test_valid_data(self):
        """ Serializer accepts valid data and returns expected fields. """
        serializer = MessageSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save()
        self.assertEqual(message["room"], self.valid_data["room"])
        self.assertEqual(message["receiver_email"], self.valid_data["receiver_email"])
        self.assertEqual(message["text"], self.valid_data["text"])
        self.assertFalse(message["is_read"])
        self.assertIsInstance(message["timestamp"], datetime)

    def test_invalid_receiver_email(self):
        """ Serializer rejects invalid email format in receiver_email. """
        data = self.valid_data.copy()
        data["receiver_email"] = "not-an-email"
        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("receiver_email", serializer.errors)

    def test_too_short_text(self):
        """ Serializer rejects text shorter than MIN_MESSAGE_LENGTH. """
        data = self.valid_data.copy()
        data["text"] = "a"  # shorter than allowed
        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors)

    def test_too_long_text(self):
        """ Serializer rejects text longer than MAX_MESSAGE_LENGTH. """
        data = self.valid_data.copy()
        data["text"] = "a" * 1001  # exceeds max length
        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors)

    def test_is_read_default_false(self):
        """ is_read must be False by default if not provided. """
        serializer = MessageSerializer(data=self.valid_data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        self.assertFalse(message["is_read"])

    def test_timestamp_is_auto_generated(self):
        """ Serializer automatically generates timestamp on save(). """
        serializer = MessageSerializer(data=self.valid_data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save()
        self.assertLessEqual(message["timestamp"], datetime.now(timezone.utc))

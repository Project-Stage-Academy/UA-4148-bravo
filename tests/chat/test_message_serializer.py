from django.test import TestCase
from chat.serializers import MessageSerializer, RoomSerializer
from core.settings.constants import FORBIDDEN_WORDS_SET

TEST_EMAIL_1 = "user1@example.com"
TEST_EMAIL_2 = "user2@example.com"
TEST_EMAIL_3 = "user3@example.com"


class MessageSerializerTestCase(TestCase):

    def setUp(self):
        """
        Set up group and private rooms for testing.
        """
        room_data = {
            "name": "GroupRoom",
            "is_group": True,
            "participants": [TEST_EMAIL_1, TEST_EMAIL_2]
        }
        serializer = RoomSerializer(data=room_data)
        serializer.is_valid(raise_exception=True)
        self.group_room = serializer.save()

        room_data = {
            "name": "PrivateRoom",
            "is_group": False,
            "participants": [TEST_EMAIL_1, TEST_EMAIL_2]
        }
        serializer = RoomSerializer(data=room_data)
        serializer.is_valid(raise_exception=True)
        self.private_room = serializer.save()

    def test_valid_group_message_no_receiver(self):
        """Group message without receiver_email should be valid."""
        data = {
            "room": self.group_room.name,
            "sender_email": TEST_EMAIL_1,
            "text": "Hello everyone!"
        }
        serializer = MessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save()
        self.assertEqual(message.text, "Hello everyone!")

    def test_valid_group_message_with_receiver(self):
        """Group message with receiver in participants should be valid."""
        data = {
            "room": self.group_room.name,
            "sender_email": TEST_EMAIL_1,
            "receiver_email": TEST_EMAIL_2,
            "text": "Hi user2!"
        }
        serializer = MessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save()
        self.assertEqual(message.receiver_email, TEST_EMAIL_2)

    def test_group_message_invalid_receiver(self):
        """Group message with receiver not in participants should raise ValidationError."""
        data = {
            "room": self.group_room.name,
            "sender_email": TEST_EMAIL_1,
            "receiver_email": TEST_EMAIL_3,
            "text": "Hi user3!"
        }
        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_private_message_valid(self):
        """Private message with valid receiver should be valid."""
        data = {
            "room": self.private_room.name,
            "sender_email": TEST_EMAIL_1,
            "receiver_email": TEST_EMAIL_2,
            "text": "Private hello!"
        }
        serializer = MessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save()
        self.assertEqual(message.text, "Private hello!")

    def test_private_message_missing_receiver(self):
        """Private message without receiver should raise ValidationError."""
        data = {
            "room": self.private_room.name,
            "sender_email": TEST_EMAIL_1,
            "text": "No receiver"
        }
        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_sender_not_in_room(self):
        """Message from a sender not in room should raise ValidationError."""
        data = {
            "room": self.group_room.name,
            "sender_email": TEST_EMAIL_3,
            "text": "Hi!"
        }
        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_empty_text_message(self):
        """Message with empty text should raise ValidationError."""
        data = {
            "room": self.group_room.name,
            "sender_email": TEST_EMAIL_1,
            "text": "   "
        }
        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors)

    def test_forbidden_words(self):
        """Message containing forbidden words should raise ValidationError."""
        forbidden_word = next(iter(FORBIDDEN_WORDS_SET)) if FORBIDDEN_WORDS_SET else "badword"
        data = {
            "room": self.group_room.name,
            "sender_email": TEST_EMAIL_1,
            "text": f"This contains {forbidden_word}"
        }
        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors)

    def test_spam_repeated_chars(self):
        """Message with repeated characters (spam) should raise ValidationError."""
        data = {
            "room": self.group_room.name,
            "sender_email": TEST_EMAIL_1,
            "text": "bbbbbbbbbbbbbbbb"
        }
        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("text", serializer.errors)

    def test_text_html_escape(self):
        """Message text should be HTML-escaped when saved."""
        data = {
            "room": self.group_room.name,
            "sender_email": TEST_EMAIL_1,
            "text": "<Hello & Welcome>"
        }
        serializer = MessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save()
        self.assertEqual(message.text, "&lt;Hello &amp; Welcome&gt;")

    def test_missing_room(self):
        """Message without room field should raise ValidationError."""
        data = {
            "sender_email": TEST_EMAIL_1,
            "text": "No room!"
        }
        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_nonexistent_room(self):
        """Message with a room that does not exist should raise ValidationError."""
        data = {
            "room": "UnknownRoom",
            "sender_email": TEST_EMAIL_1,
            "text": "Unknown room"
        }
        serializer = MessageSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_update_text_escape(self):
        """Updating message text should apply HTML-escape."""
        data = {
            "room": self.group_room.name,
            "sender_email": TEST_EMAIL_1,
            "text": "Hello"
        }
        serializer = MessageSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        message = serializer.save()

        new_data = {
            "room": self.group_room.name,
            "sender_email": TEST_EMAIL_1,
            "text": "<Updated & Text>"
        }
        update_serializer = MessageSerializer(instance=message, data=new_data)
        self.assertTrue(update_serializer.is_valid(), update_serializer.errors)
        updated_msg = update_serializer.save()
        self.assertEqual(updated_msg.text, "&lt;Updated &amp; Text&gt;")

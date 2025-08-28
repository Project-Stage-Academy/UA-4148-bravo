from django.test import TestCase
from chat.serializers import RoomSerializer

TEST_EMAIL_1 = "user1@example.com"
TEST_EMAIL_2 = "user2@example.com"
TEST_EMAIL_3 = "user3@example.com"


class RoomSerializerTestCase(TestCase):

    def test_valid_room_creation(self):
        """Room with valid name and participants should be valid."""
        data = {
            "name": "MyRoom",
            "is_group": True,
            "participants": [TEST_EMAIL_1, TEST_EMAIL_2]
        }
        serializer = RoomSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["name"], "MyRoom")
        self.assertEqual(serializer.validated_data["participants"], [TEST_EMAIL_1, TEST_EMAIL_2])

    def test_name_html_escape(self):
        """Room name should be stripped and HTML-escaped."""
        data = {
            "name": "  <Room&Name>  ",
            "is_group": True,
            "participants": [TEST_EMAIL_1, TEST_EMAIL_2]
        }
        serializer = RoomSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["name"], "&lt;Room&amp;Name&gt;")

    def test_name_length_constraints(self):
        """Room name below min_length or above max_length should fail."""
        short_name_data = {
            "name": "AB",
            "is_group": True,
            "participants": [TEST_EMAIL_1, TEST_EMAIL_2]
        }
        long_name_data = {
            "name": "A" * 51,
            "is_group": True,
            "participants": [TEST_EMAIL_1, TEST_EMAIL_2]
        }
        serializer = RoomSerializer(data=short_name_data)
        self.assertFalse(serializer.is_valid())
        serializer = RoomSerializer(data=long_name_data)
        self.assertFalse(serializer.is_valid())

    def test_empty_participants_list(self):
        """Participants list cannot be empty."""
        data = {
            "name": "MyRoom",
            "is_group": True,
            "participants": []
        }
        serializer = RoomSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("participants", serializer.errors)

    def test_duplicate_participants_removed(self):
        """Serializer should remove duplicate emails preserving order."""
        data = {
            "name": "MyRoom",
            "is_group": True,
            "participants": [TEST_EMAIL_1, TEST_EMAIL_2, TEST_EMAIL_1]
        }
        serializer = RoomSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["participants"], [TEST_EMAIL_1, TEST_EMAIL_2])

    def test_max_participants_limit(self):
        """Serializer should reject rooms with participants exceeding MAX_PARTICIPANTS."""
        from chat.serializers import MAX_PARTICIPANTS
        participants = [f"user{i}@example.com" for i in range(MAX_PARTICIPANTS + 1)]
        data = {"name": "BigRoom", "is_group": True, "participants": participants}
        serializer = RoomSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("participants", serializer.errors)

    def test_private_room_participant_count(self):
        """Private rooms must have exactly 2 participants."""
        data = {"name": "Private1", "is_group": False, "participants": [TEST_EMAIL_1]}
        serializer = RoomSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        data = {"name": "Private2", "is_group": False, "participants": [TEST_EMAIL_1, TEST_EMAIL_2, TEST_EMAIL_3]}
        serializer = RoomSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        data = {"name": "Private3", "is_group": False, "participants": [TEST_EMAIL_1, TEST_EMAIL_2]}
        serializer = RoomSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_fields(self):
        """Serializer should fail if required fields are missing."""
        serializer = RoomSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
        self.assertIn("participants", serializer.errors)

    def test_name_with_only_spaces(self):
        """Name with only spaces should be escaped to empty string."""
        data = {"name": "   ", "is_group": True, "participants": [TEST_EMAIL_1, TEST_EMAIL_2]}
        serializer = RoomSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["name"], "")

    def test_update_room(self):
        """Updating room should correctly update fields."""
        data = {"name": "Room1", "is_group": True, "participants": [TEST_EMAIL_1, TEST_EMAIL_2]}
        serializer = RoomSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        room_instance = serializer.create(serializer.validated_data)

        update_data = {"name": "<NewName>", "is_group": False, "participants": [TEST_EMAIL_1, TEST_EMAIL_2]}
        updated_serializer = RoomSerializer(instance=room_instance, data=update_data)
        self.assertTrue(updated_serializer.is_valid())
        updated_room = updated_serializer.update(room_instance, updated_serializer.validated_data)
        self.assertEqual(updated_room.name, "&lt;NewName&gt;")
        self.assertFalse(updated_room.is_group)

    def test_invalid_email_in_participants(self):
        """Serializer should reject invalid email addresses in participants list."""
        data = {
            "name": "RoomInvalidEmail",
            "is_group": True,
            "participants": [TEST_EMAIL_1, "invalid-email"]
        }
        serializer = RoomSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("participants", serializer.errors)

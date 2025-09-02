from chat.serializers import RoomSerializer
from tests.chat.test_create_users import BaseChatTestCase, TEST_EMAIL_1, TEST_EMAIL_2, TEST_EMAIL_3


class RoomSerializerTestCase(BaseChatTestCase):

    def test_valid_room_creation(self):
        """Room with valid name and participants should be valid."""
        data = {
            "name": "MyRoom",
            "participants": [TEST_EMAIL_1, TEST_EMAIL_2]
        }
        serializer = RoomSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["name"], "MyRoom")
        self.assertEqual(serializer.validated_data["participants"], [TEST_EMAIL_1, TEST_EMAIL_2])

    def test_name_length_constraints(self):
        """Room name below min_length or above max_length should fail."""
        short_name_data = {
            "name": "AB",
            "participants": [TEST_EMAIL_1, TEST_EMAIL_2]
        }
        long_name_data = {
            "name": "A" * 51,
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
            "participants": []
        }
        serializer = RoomSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("participants", serializer.errors)

    def test_missing_fields(self):
        """Serializer should fail if required fields are missing."""
        serializer = RoomSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
        self.assertIn("participants", serializer.errors)

    def test_invalid_email_in_participants(self):
        """Serializer should reject invalid email addresses in participants list."""
        data = {
            "name": "RoomInvalidEmail",
            "participants": [TEST_EMAIL_1, "invalid-email"]
        }
        serializer = RoomSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("participants", serializer.errors)

    def test_update_room(self):
        """Updating room should correctly update fields."""
        data = {"name": "Room1", "participants": [TEST_EMAIL_1, TEST_EMAIL_2]}
        serializer = RoomSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        room_instance = serializer.create(serializer.validated_data)

        update_data = {"name": "NewName", "participants": [TEST_EMAIL_1, TEST_EMAIL_3]}
        updated_serializer = RoomSerializer(instance=room_instance, data=update_data)
        self.assertTrue(updated_serializer.is_valid())
        updated_room = updated_serializer.update(room_instance, updated_serializer.validated_data)
        self.assertEqual(updated_room.name, "NewName")
        self.assertEqual(updated_room.participants, [TEST_EMAIL_1, TEST_EMAIL_3])

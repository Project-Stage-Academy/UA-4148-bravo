from rest_framework import status
from chat.documents import Room, Message
from tests.chat.test_api_base_case import BaseChatTestCase


class ConversationCreateViewTests(BaseChatTestCase):
    def setUp(self):
        super().setUp()
        self.url = 'api/v1/chat/conversations/'

    def test_create_room_success(self):
        """Test creating a valid private conversation."""
        data = {
            'name': 'investor_startup_chat',
            'participants': ['investor@example.com', 'startup@example.com']
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'], data['name'])
        self.assertEqual(len(response.data['participants']), 2)

    def test_create_room_invalid_participants(self):
        """Test room creation fails if participants are not exactly 2."""
        data = {
            'name': 'invalid_room',
            'participants': ['only_one@example.com']
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Private room must have exactly 2 participants.')

    def test_create_room_duplicate_name(self):
        """Test room creation fails if room name already exists."""
        Room(name='existing_room', participants=['a@example.com', 'b@example.com']).save()
        data = {
            'name': 'existing_room',
            'participants': ['c@example.com', 'd@example.com']
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_unauthenticated_access(self):
        """Test that unauthenticated user cannot create a room."""
        self.client.cookies.clear()
        data = {
            'name': 'new_room',
            'participants': ['a@example.com', 'b@example.com']
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SendMessageViewTests(BaseChatTestCase):
    def setUp(self):
        super().setUp()
        self.url = 'api/v1/chat/messages/'

    def test_send_message_success_existing_room(self):
        """Test sending message in an existing room."""
        Room(name='chat_room', participants=['sender@example.com', 'receiver@example.com']).save()
        data = {
            'room': 'chat_room',
            'sender_email': 'sender@example.com',
            'receiver_email': 'receiver@example.com',
            'text': 'Hello!'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['text'], 'Hello!')
        self.assertIn('room', response.data)
        self.mock_group_send.assert_called_once()

    def test_send_message_success_create_room(self):
        """Test sending message when room does not exist, room should be auto-created."""
        data = {
            'room': 'new_room',
            'sender_email': 'sender@example.com',
            'receiver_email': 'receiver@example.com',
            'text': 'Hi there!'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        room = Room.objects(name='new_room').first()
        self.assertIsNotNone(room)
        self.assertEqual(set(room.participants), {'sender@example.com', 'receiver@example.com'})

    def test_send_message_user_not_participant(self):
        """Test sending message fails if sender is not a participant."""
        Room(name='room1', participants=['other@example.com', 'receiver@example.com']).save()
        data = {
            'room': 'room1',
            'sender_email': 'sender@example.com',
            'receiver_email': 'receiver@example.com',
            'text': 'Hello!'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], 'You are not a participant of this room.')

    def test_send_message_invalid_participants_for_new_room(self):
        """Test new room creation fails if participants count != 2."""
        data = {
            'room': 'invalid_room',
            'sender_email': 'sender@example.com',
            'receiver_email': 'sender@example.com',  # same email
            'text': 'Hello!'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Private room must have exactly 2 participants.')

    def test_send_message_unauthenticated(self):
        """Test sending message fails if user is not authenticated."""
        self.client.cookies.clear()
        data = {
            'room': 'chat_room',
            'sender_email': 'sender@example.com',
            'receiver_email': 'receiver@example.com',
            'text': 'Hello!'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ConversationMessagesViewTests(BaseChatTestCase):
    def setUp(self):
        super().setUp()
        self.base_url = 'api/v1/chat/conversations/'

    def _get_messages_url(self, room_name):
        return f"{self.base_url}{room_name}/messages/"

    def test_get_messages_success(self):
        """Test retrieving messages for a room the user participates in."""
        room = Room(name='friends_group', participants=['sender@example.com', 'receiver@example.com']).save()
        Message(room=room, sender_email='sender@example.com', receiver_email='receiver@example.com',
                text='Hello everyone!').save()
        Message(room=room, sender_email='receiver@example.com', receiver_email='sender@example.com', text='Hi!').save()

        url = self._get_messages_url('friends_group')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['text'], 'Hello everyone!')
        self.assertEqual(response.data[1]['text'], 'Hi!')

    def test_get_messages_room_not_exist(self):
        """Test 404 returned if room does not exist."""
        url = self._get_messages_url('nonexistent_room')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_messages_user_not_participant(self):
        """Test 404 returned if user is not a participant of the room."""
        Room(name='private_room', participants=['other@example.com', 'another@example.com']).save()
        url = self._get_messages_url('private_room')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_messages_unauthenticated(self):
        """Test that unauthenticated user cannot access messages."""
        self.client.cookies.clear()
        Room(name='friends_group', participants=['sender@example.com', 'receiver@example.com']).save()
        url = self._get_messages_url('friends_group')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

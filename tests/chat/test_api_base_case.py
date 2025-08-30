from rest_framework.test import APITestCase, APIClient
from users.models import User, UserRole
from chat.documents import Room, Message
from mongoengine import connect, disconnect
from unittest.mock import patch, MagicMock
import mongomock


class BaseChatTestCase(APITestCase):
    """ Base class for chat view tests, with JWT and MongoEngine mocks. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        role, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
        self.user = User.objects.create_user(
            email='sender@example.com',
            password='password123',
            first_name="Sender",
            last_name="User",
            user_phone="+123456789",
            title="Developer",
            role=role,
            is_active=True
        )
        self.client = APIClient()
        self.client.cookies['access_token'] = 'fake-jwt-token-for-test'

        self.patcher_decode = patch('users.cookie_jwt.safe_decode', return_value={'user_id': str(self.user.id)})
        self.mock_decode = self.patcher_decode.start()

        self.patcher_channel = patch('chat.views.base_protected_view.get_channel_layer')
        self.mock_channel_layer = self.patcher_channel.start()
        self.mock_group_send = MagicMock()
        self.mock_channel_layer.return_value.group_send = self.mock_group_send

    def tearDown(self):
        self.patcher_decode.stop()
        self.patcher_channel.stop()
        Room.objects.delete()
        Message.objects.delete()
        User.objects.delete()

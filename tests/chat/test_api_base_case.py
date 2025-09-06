import os
from rest_framework.test import APITestCase, APIClient
from users.models import User, UserRole
from chat.documents import Room, Message
from mongoengine import connect, disconnect
from unittest.mock import patch, AsyncMock
import mongomock

TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


class BaseChatTestCase(APITestCase):
    """ Base class for chat view tests, with JWT and MongoEngine mocks. """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        connect(
            db="mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="chat_test"
        )

    @classmethod
    def tearDownClass(cls):
        disconnect(alias="chat_test")
        super().tearDownClass()

    def setUp(self):
        role, _ = UserRole.objects.get_or_create(role=UserRole.Role.STARTUP)
        self.user = User.objects.create_user(
            email='sender@example.com',
            password=TEST_USER_PASSWORD,
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

        self.patcher_channel = patch('chat.views.get_channel_layer')
        self.mock_channel_layer = self.patcher_channel.start()

        mock_layer_instance = self.mock_channel_layer.return_value
        self.mock_group_send = AsyncMock()
        mock_layer_instance.group_send = self.mock_group_send

    def tearDown(self):
        self.patcher_decode.stop()
        self.patcher_channel.stop()
        Room.objects.delete()
        Message.objects.delete()
        User.objects.all().delete()

    def create_roles(self):
        """Ensure startup & investor roles exist and return them."""
        role_startup, _ = UserRole.objects.get_or_create(role=UserRole.Role.STARTUP)
        role_investor, _ = UserRole.objects.get_or_create(role=UserRole.Role.INVESTOR)
        return role_startup, role_investor

    def create_user(self, email, role, password="password123", **kwargs):
        """Shortcut for creating a user."""
        defaults = dict(
            first_name="Test",
            last_name="User",
            role=role,
            is_active=True,
        )
        defaults.update(kwargs)
        return User.objects.create_user(email=email, password=password, **defaults)

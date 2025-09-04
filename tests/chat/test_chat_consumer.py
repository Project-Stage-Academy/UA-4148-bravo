import asyncio
import os
from unittest.mock import MagicMock, patch, AsyncMock
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase
from mongoengine.errors import DoesNotExist
from mongoengine.errors import ValidationError as MongoValidationError
from chat.consumers import InvestorStartupMessageConsumer
from chat.documents import Message, Room, MAX_MESSAGE_LENGTH
from users.models import UserRole, User
from mongoengine import connect, disconnect
import mongomock

TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


class InvestorStartupMessageConsumerTest(TransactionTestCase):
    """
    Comprehensive tests for InvestorStartupMessageConsumer.

    Includes:
        - WebSocket integration tests (connect, send, validations, rate limit)
        - Unit tests for get_or_create_chat_room and save_message
    """

    reset_sequences = True

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
        """
        Prepare mock users and event loop for async calls.
        """
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        role_startup, _ = UserRole.objects.get_or_create(role=UserRole.Role.STARTUP)
        role_investor, _ = UserRole.objects.get_or_create(role=UserRole.Role.INVESTOR)

        self.startup = User.objects.create_user(
            email="startup@example.com",
            password=TEST_USER_PASSWORD,
            first_name="First",
            last_name="User",
            role=role_startup,
        )
        self.investor = User.objects.create_user(
            email="investor@example.com",
            password=TEST_USER_PASSWORD,
            first_name="Second",
            last_name="User",
            role=role_investor,
        )

        self.mock_investor = MagicMock(spec=User, email="investor@example.com")
        self.mock_investor.role = MagicMock()
        self.mock_investor.role.role = UserRole.Role.INVESTOR

        self.mock_startup = MagicMock(spec=User, email="startup@example.com")
        self.mock_startup.role = MagicMock()
        self.mock_startup.role.role = UserRole.Role.STARTUP

    def tearDown(self):
        self.loop.close()

    async def try_receive(self, communicator, timeout=0.5):
        """
        Helper: safely try to receive a message.
        Returns None if timeout occurs.
        """
        try:
            return await asyncio.wait_for(communicator.receive_json_from(), timeout=timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            return None

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_or_create_chat_room", new_callable=AsyncMock)
    @patch("chat.consumers.InvestorStartupMessageConsumer.get_user_by_email", new_callable=AsyncMock)
    @patch("chat.consumers.InvestorStartupMessageConsumer.save_message", new_callable=AsyncMock)
    def test_connect_and_send_message(self, save_mock, get_user_mock, get_or_create_mock):
        get_user_mock.return_value = self.startup
        room_mock = MagicMock(id="roomid", name="roomname", participants=[self.investor.email, self.startup.email])
        get_or_create_mock.return_value = (room_mock, True)
        save_mock.return_value = MagicMock(text="Hello")

        communicator = WebsocketCommunicator(
            InvestorStartupMessageConsumer.as_asgi(),
            f"/ws/chat/{self.startup.email}/"
        )
        communicator.scope["user"] = self.investor
        communicator.scope["url_route"] = {"kwargs": {"other_user_email": self.startup.email}}

        connected = self.loop.run_until_complete(communicator.connect())
        self.assertTrue(connected)

        self.loop.run_until_complete(communicator.send_json_to({"message": "Hello"}))
        response = self.loop.run_until_complete(self.try_receive(communicator))
        self.assertEqual(response["message"], "Hello")
        self.assertEqual(response["sender"], self.investor.email)
        save_mock.assert_awaited_once()
        self.loop.run_until_complete(communicator.disconnect())

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_user_by_email", new_callable=AsyncMock)
    def test_connect_user_not_found(self, get_user_mock):
        get_user_mock.return_value = None

        communicator = WebsocketCommunicator(
            InvestorStartupMessageConsumer.as_asgi(),
            f"/ws/chat/{self.startup.email}/"
        )
        communicator.scope["user"] = self.investor
        communicator.scope["url_route"] = {"kwargs": {"other_user_email": self.startup.email}}

        connected, _ = self.loop.run_until_complete(communicator.connect())
        self.assertFalse(connected)

    def test_connect_unauthenticated(self):
        communicator = WebsocketCommunicator(
            InvestorStartupMessageConsumer.as_asgi(),
            f"/ws/chat/{self.startup.email}/"
        )
        communicator.scope["user"] = AnonymousUser()
        communicator.scope["url_route"] = {"kwargs": {"other_user_email": self.startup.email}}

        connected, _ = self.loop.run_until_complete(communicator.connect())
        self.assertFalse(connected)

    def async_try_receive(self, communicator, timeout=1):
        async def inner():
            try:
                return await asyncio.wait_for(communicator.receive_json_from(), timeout=timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                return None
        return inner()

    def setup_communicator(self, get_or_create_mock, room_mock):
        get_or_create_mock.return_value = (room_mock, True)
        communicator = WebsocketCommunicator(
            InvestorStartupMessageConsumer.as_asgi(),
            f"/ws/chat/{self.startup.email}/"
        )
        communicator.scope["user"] = self.investor
        communicator.scope["url_route"] = {"kwargs": {"other_user_email": self.startup.email}}
        connected = asyncio.get_event_loop().run_until_complete(communicator.connect())
        self.assertTrue(connected)
        return communicator

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_user_by_email", new_callable=AsyncMock)
    @patch("chat.consumers.InvestorStartupMessageConsumer.get_or_create_chat_room", new_callable=AsyncMock)
    def test_forbidden_words(self, get_or_create_mock, get_user_mock):
        get_user_mock.return_value = self.startup
        room_mock = MagicMock(id="roomid", name="roomname", participants=[self.investor.email, self.startup.email])
        communicator = self.setup_communicator(get_or_create_mock, room_mock)

        with patch("chat.consumers.FORBIDDEN_WORDS_SET", {"forbiddenword"}):
            self.loop.run_until_complete(
                communicator.send_json_to({"message": "Contains forbiddenword"})
            )
            response = self.loop.run_until_complete(self.async_try_receive(communicator))
            self.assertIsNotNone(response)
            self.assertEqual(response["error"], "Message contains forbidden content")

        self.loop.run_until_complete(communicator.disconnect())

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_user_by_email", new_callable=AsyncMock)
    @patch("chat.consumers.InvestorStartupMessageConsumer.get_or_create_chat_room", new_callable=AsyncMock)
    def test_empty_message_ignored(self, get_or_create_mock, get_user_mock):
        get_user_mock.return_value = self.startup
        room_mock = MagicMock(id="roomid", name="roomname", participants=[self.investor.email, self.startup.email])
        communicator = self.setup_communicator(get_or_create_mock, room_mock)

        self.loop.run_until_complete(communicator.send_json_to({"message": ""}))

        response = self.loop.run_until_complete(self.async_try_receive(communicator, timeout=0.2))
        self.assertIsNone(response)

        try:
            self.loop.run_until_complete(communicator.disconnect())
        except asyncio.CancelledError:
            pass

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_user_by_email", new_callable=AsyncMock)
    @patch("chat.consumers.InvestorStartupMessageConsumer.get_or_create_chat_room", new_callable=AsyncMock)
    def test_message_too_long(self, get_or_create_mock, get_user_mock):
        get_user_mock.return_value = self.startup
        room_mock = MagicMock(id="roomid", name="roomname", participants=[self.investor.email, self.startup.email])
        communicator = self.setup_communicator(get_or_create_mock, room_mock)

        long_msg = "x" * (MAX_MESSAGE_LENGTH + 1)
        self.loop.run_until_complete(communicator.send_json_to({"message": long_msg}))
        response = self.loop.run_until_complete(self.async_try_receive(communicator))
        self.assertIsNotNone(response)
        self.assertIn("Message length must be", response["error"])

        self.loop.run_until_complete(communicator.disconnect())

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_user_by_email", new_callable=AsyncMock)
    @patch("chat.consumers.InvestorStartupMessageConsumer.get_or_create_chat_room", new_callable=AsyncMock)
    def test_spam_message(self, get_or_create_mock, get_user_mock):
        get_user_mock.return_value = self.startup
        room_mock = MagicMock(id="roomid", name="roomname", participants=[self.investor.email, self.startup.email])
        communicator = self.setup_communicator(get_or_create_mock, room_mock)

        spam_msg = "b" * 12
        self.loop.run_until_complete(communicator.send_json_to({"message": spam_msg}))
        response = self.loop.run_until_complete(self.async_try_receive(communicator))
        self.assertIsNotNone(response)
        self.assertEqual(response["error"], "Message looks like spam")

        self.loop.run_until_complete(communicator.disconnect())

    @patch("chat.consumers.Room.objects.get")
    @patch("chat.consumers.Room.save", autospec=True)
    def test_create_room_if_not_exists(self, mock_save, mock_get):
        mock_get.side_effect = DoesNotExist

        consumer = InvestorStartupMessageConsumer()
        room, created = self.loop.run_until_complete(
            consumer.get_or_create_chat_room(self.startup, self.investor)
        )

        self.assertTrue(created)
        self.assertIn(self.investor.email, room.participants)
        self.assertIn(self.startup.email, room.participants)
        mock_save.assert_called_once_with(room)

    def test_invalid_roles_raises_validation_error(self):
        """
        Test that get_or_create_chat_room raises ValidationError when roles are invalid.

        Uses two investors to trigger invalid role combination.
        """
        other = MagicMock(spec=User)
        other.role = MagicMock()
        other.role.role = "Investor"
        other.email = "other@example.com"

        consumer = InvestorStartupMessageConsumer()
        with self.assertRaises(MongoValidationError):
            self.loop.run_until_complete(
                consumer.get_or_create_chat_room(self.investor, other)
            )

    def test_save_message_adds_missing_participants(self):
        consumer = InvestorStartupMessageConsumer()
        consumer.user = self.investor
        consumer.other_user = self.startup

        room_mock = MagicMock(spec=Room)
        room_mock.participants = [self.investor.email]
        room_mock.save = MagicMock()
        consumer.room = room_mock

        msg_instance_mock = MagicMock(spec=Message)
        msg_instance_mock.save = MagicMock()

        with patch("chat.consumers.Message", return_value=msg_instance_mock):
            result = self.loop.run_until_complete(consumer.save_message("Hello"))
            self.assertEqual(result, msg_instance_mock)
            self.assertIn(self.startup.email, consumer.room.participants)
            room_mock.save.assert_called_once()
            msg_instance_mock.save.assert_called_once()

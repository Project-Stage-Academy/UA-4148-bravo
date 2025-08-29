import asyncio
from unittest.mock import patch, MagicMock
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from chat.consumers import InvestorStartupMessageConsumer
from users.models import User
from django.contrib.auth.models import AnonymousUser
from chat.consumers import MAX_MESSAGE_LENGTH, MIN_MESSAGE_LENGTH, MESSAGE_RATE_LIMIT


class InvestorStartupMessageConsumerTest(TransactionTestCase):
    """
    Unit tests for InvestorStartupMessageConsumer using Django's TransactionTestCase
    and Channels WebSocket testing utilities.

    Tests cover:
        - WebSocket connection handling for authenticated and unauthenticated users
        - Handling user not found cases
        - Sending and receiving messages with proper validations
        - Rate limiting enforcement
        - Room creation and message persistence
    """

    reset_sequences = True

    def setUp(self):
        """
        Create mock users for testing purposes and initialize a shared asyncio event loop.
        """
        self.investor = User.objects.create_user(email="investor@example.com", password="pass")
        self.startup = User.objects.create_user(email="startup@example.com", password="pass")

        self.investor.roles = MagicMock()
        self.startup.roles = MagicMock()
        self.investor.roles.filter.return_value.exists.side_effect = lambda name=None: name == "Investor"
        self.startup.roles.filter.return_value.exists.side_effect = lambda name=None: name == "Startup"

        self.loop = asyncio.get_event_loop()

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_or_create_chat_room")
    @patch("chat.consumers.InvestorStartupMessageConsumer.get_user_by_email")
    @patch("chat.consumers.InvestorStartupMessageConsumer.save_message")
    def test_connect_and_send_message(self, save_mock, get_user_mock, get_or_create_mock):
        """
        Test full flow of connecting to a chat, sending a valid message,
        and receiving it via WebSocket.

        Mocks:
            - User retrieval
            - Room creation
            - Message persistence
        """
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

        connected, _ = self.loop.run_until_complete(communicator.connect())
        self.assertTrue(connected)

        self.loop.run_until_complete(communicator.send_json_to({"message": "Hello"}))
        response = self.loop.run_until_complete(communicator.receive_json_from())
        self.assertEqual(response["message"], "Hello")
        self.assertEqual(response["sender"], self.investor.email)

        save_mock.assert_awaited_once()
        self.loop.run_until_complete(communicator.disconnect())

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_user_by_email")
    def test_connect_user_not_found(self, get_user_mock):
        """
        Test WebSocket connection is rejected when the other user does not exist.
        """
        get_user_mock.return_value = None
        communicator = WebsocketCommunicator(
            InvestorStartupMessageConsumer.as_asgi(),
            f"/ws/chat/{self.startup.email}/"
        )
        communicator.scope["user"] = self.investor
        communicator.scope["url_route"] = {"kwargs": {"other_user_email": self.startup.email}}

        connected, _ = self.loop.run_until_complete(communicator.connect())
        self.assertFalse(connected)

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_or_create_chat_room")
    def test_connect_unauthenticated(self, get_or_create_mock):
        """
        Test WebSocket connection is rejected for unauthenticated users.
        """
        get_or_create_mock.side_effect = Exception("Should not be called")

        communicator = WebsocketCommunicator(
            InvestorStartupMessageConsumer.as_asgi(),
            f"/ws/chat/{self.startup.email}/"
        )
        communicator.scope["user"] = AnonymousUser()
        communicator.scope["url_route"] = {"kwargs": {"other_user_email": self.startup.email}}

        connected, _ = self.loop.run_until_complete(communicator.connect())
        self.assertFalse(connected)

    async def try_receive(self, communicator, timeout=0.1):
        """
        Securely receive message. Returns None if timeout.
        """
        try:
            return await communicator.receive_json_from(timeout=timeout)
        except asyncio.TimeoutError:
            return None

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_or_create_chat_room")
    @patch("chat.consumers.InvestorStartupMessageConsumer.get_user_by_email")
    @patch("chat.consumers.InvestorStartupMessageConsumer.save_message")
    def test_message_validations(self, save_mock, get_user_mock, get_or_create_mock):
        """
        Tests all message validation rules in InvestorStartupMessageConsumer:
        - Forbidden words
        - Empty messages
        - Messages exceeding max length
        - Spam detection
        - Rate limiting
        """
        get_user_mock.return_value = self.startup
        room_mock = MagicMock(
            id="roomid",
            name="roomname",
            participants=[self.investor.email, self.startup.email]
        )
        get_or_create_mock.return_value = (room_mock, True)

        async def async_save_message(message_text):
            msg = MagicMock()
            msg.text = message_text
            return msg

        save_mock.side_effect = async_save_message

        communicator = WebsocketCommunicator(
            InvestorStartupMessageConsumer.as_asgi(),
            f"/ws/chat/{self.startup.email}/"
        )
        communicator.scope["user"] = self.investor
        communicator.scope["url_route"] = {"kwargs": {"other_user_email": self.startup.email}}

        connected, _ = self.loop.run_until_complete(communicator.connect())
        self.assertTrue(connected)

        with patch("chat.consumers.FORBIDDEN_WORDS_SET", {"forbiddenword"}):
            self.loop.run_until_complete(
                communicator.send_json_to({"message": "This contains forbiddenword"})
            )
            response = self.loop.run_until_complete(communicator.receive_json_from())
            self.assertIsNotNone(response)
            self.assertIn("error", response)
            self.assertEqual(response["error"], "Message contains forbidden content")

        self.loop.run_until_complete(communicator.send_json_to({"message": ""}))
        response = self.loop.run_until_complete(communicator.receive_nothing())
        self.assertTrue(response)

        self.loop.run_until_complete(
            communicator.send_json_to({"message": "x" * (MAX_MESSAGE_LENGTH + 1)})
        )
        response = self.loop.run_until_complete(communicator.receive_json_from())
        self.assertIsNotNone(response)
        self.assertIn("error", response)
        self.assertEqual(
            response["error"],
            f"Message length must be {MIN_MESSAGE_LENGTH}-{MAX_MESSAGE_LENGTH} chars"
        )

        self.loop.run_until_complete(
            communicator.send_json_to({"message": "bbbbbbbbbbbb"})
        )
        response = self.loop.run_until_complete(communicator.receive_json_from())
        self.assertIsNotNone(response)
        self.assertIn("error", response)
        self.assertEqual(response["error"], "Message looks like spam")

        for i in range(MESSAGE_RATE_LIMIT):
            self.loop.run_until_complete(
                communicator.send_json_to({"message": f"Hello {i}"})
            )
            response = self.loop.run_until_complete(communicator.receive_json_from())
            self.assertIsNotNone(response)
            self.assertIn("message", response)
            self.assertEqual(response["message"], f"Hello {i}")
            self.assertEqual(response["sender"], self.investor.email)

        self.loop.run_until_complete(
            communicator.send_json_to({"message": "Hello rate limit"})
        )
        response = self.loop.run_until_complete(communicator.receive_json_from())
        self.assertIsNotNone(response)
        self.assertIn("error", response)
        self.assertIn("Rate limit exceeded", response["error"])

        self.loop.run_until_complete(
            communicator.send_json_to({"message": "Hello after limit"})
        )
        response = self.loop.run_until_complete(self.try_receive(communicator))
        self.assertIsNotNone(response)
        self.assertIn("error", response)
        self.assertIn("Rate limit exceeded", response["error"])

import os
from unittest.mock import patch, MagicMock
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase
from chat.consumers import InvestorStartupMessageConsumer
from users.models import User
from django.contrib.auth.models import AnonymousUser

MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 1000))
MESSAGE_RATE_LIMIT = int(os.getenv("MESSAGE_RATE_LIMIT", 5))


class InvestorStartupMessageConsumerTest(TransactionTestCase):
    """
    Unit tests for InvestorStartupMessageConsumer using Django's TransactionTestCase
    and Channels WebSocket testing tools.

    Covers:
        - Connection handling (authenticated, unauthenticated, user not found)
        - Sending and receiving messages via WebSocket
        - Proper invocation of room creation and message saving
    """

    reset_sequences = True

    def setUp(self):
        """
        Creates mock users for testing purposes and assigns mock roles.
        """
        self.investor = User.objects.create_user(email="investor@example.com", password="pass")
        self.startup = User.objects.create_user(email="startup@example.com", password="pass")

        self.investor.roles = MagicMock()
        self.startup.roles = MagicMock()
        self.investor.roles.filter.return_value.exists.side_effect = lambda name=None: name == "Investor"
        self.startup.roles.filter.return_value.exists.side_effect = lambda name=None: name == "Startup"

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_or_create_chat_room")
    @patch("chat.consumers.InvestorStartupMessageConsumer.get_user_by_email")
    @patch("chat.consumers.InvestorStartupMessageConsumer.save_message")
    def test_connect_and_send_message(self, save_mock, get_user_mock, get_or_create_mock):
        """
        Test the complete flow of connecting to a chat, sending a valid message,
        and receiving it through the WebSocket.

        - Mocks database interactions: user retrieval, room creation, message saving.
        - Ensures connection is successful.
        - Ensures message is broadcasted and saved correctly.
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
        Test connecting to a chat when the other user cannot be found.

        - Ensures the WebSocket connection is rejected.
        """
        get_user_mock.return_value = None
        communicator = WebsocketCommunicator(
            InvestorStartupMessageConsumer.as_asgi(),
            "/ws/chat/unknown@example.com/"
        )
        communicator.scope["user"] = self.investor
        connected, _ = self.loop.run_until_complete(communicator.connect())
        self.assertFalse(connected)

    def test_connect_unauthenticated(self):
        """
        Test connecting to a chat with an unauthenticated user.

        - Uses Django's AnonymousUser to simulate unauthenticated access.
        - Ensures the WebSocket connection is rejected.
        """
        communicator = WebsocketCommunicator(
            InvestorStartupMessageConsumer.as_asgi(),
            "/ws/chat/other@example.com/"
        )
        communicator.scope["user"] = AnonymousUser()
        connected, _ = self.loop.run_until_complete(communicator.connect())
        self.assertFalse(connected)

    @patch("chat.consumers.InvestorStartupMessageConsumer.get_or_create_chat_room")
    @patch("chat.consumers.InvestorStartupMessageConsumer.get_user_by_email")
    @patch("chat.consumers.InvestorStartupMessageConsumer.save_message")
    def test_message_validations(self, save_mock, get_user_mock, get_or_create_mock):
        """
        Tests message validation rules:
            - Forbidden words
            - Too short or too long
            - Repeated characters (spam)
            - Rate limiting
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
        self.loop.run_until_complete(communicator.connect())

        bad_message = "This contains forbiddenword"
        with patch("chat.consumers.FORBIDDEN_WORDS_SET", {"forbiddenword"}):
            self.loop.run_until_complete(communicator.send_json_to({"message": bad_message}))
            response = self.loop.run_until_complete(communicator.receive_json_from())
            self.assertIn("error", response)

        short_message = ""
        self.loop.run_until_complete(communicator.send_json_to({"message": short_message}))
        response = self.loop.run_until_complete(communicator.receive_json_from())
        self.assertIn("error", response)

        long_message = "x" * (MAX_MESSAGE_LENGTH + 1)
        self.loop.run_until_complete(communicator.send_json_to({"message": long_message}))
        response = self.loop.run_until_complete(communicator.receive_json_from())
        self.assertIn("error", response)

        spam_message = "bbbbbbbbbbbb"
        self.loop.run_until_complete(communicator.send_json_to({"message": spam_message}))
        response = self.loop.run_until_complete(communicator.receive_json_from())
        self.assertIn("error", response)

        valid_message = "Hello"
        for _ in range(MESSAGE_RATE_LIMIT + 1):
            self.loop.run_until_complete(communicator.send_json_to({"message": valid_message}))
        response = self.loop.run_until_complete(communicator.receive_json_from())
        self.assertIn("error", response)
        self.assertIn("Rate limit exceeded", response["error"])

        self.loop.run_until_complete(communicator.disconnect())

import os
from django.test import TestCase
from unittest.mock import patch
from chat.documents import Message, Room
from users.models import User, UserRole
from communications.models import Notification
from mongoengine import connect, disconnect
import mongomock

TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


class NotificationFlowTestCase(TestCase):
    """
    Tests the full notification flow:
    Message saved -> Notification created -> Celery task executed -> WS message sent.
    """

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
        role_startup, _ = UserRole.objects.get_or_create(role=UserRole.Role.STARTUP)
        role_investor, _ = UserRole.objects.get_or_create(role=UserRole.Role.INVESTOR)
        self.sender = User.objects.create_user(
            email="sender@example.com",
            password=TEST_USER_PASSWORD,
            first_name="Sender",
            last_name="User",
            role=role_startup,
        )
        self.receiver = User.objects.create_user(
            email="receiver@example.com",
            password=TEST_USER_PASSWORD,
            first_name="Receiver",
            last_name="User",
            role=role_investor,
        )

    @patch("communications.tasks.send_notification_task.delay")
    def test_message_triggers_notification_task(self, mock_send_task):
        """
        Test that creating a Message triggers a Notification and dispatches the Celery task.
        """
        room = Room(name='chat_room', participants=[self.sender.email, self.receiver.email]).save()
        message = Message(
            room=room,
            sender_email=self.sender.email,
            receiver_email=self.receiver.email,
            text="Hello, this is a test message"
        )
        message.save()

        notifications = Notification.objects.filter(recipient=self.receiver)
        self.assertEqual(notifications.count(), 1)
        notification = notifications.first()
        self.assertEqual(notification.message.text, message.text)

        mock_send_task.assert_called_once()
        args, kwargs = mock_send_task.call_args
        self.assertEqual(kwargs["user_id"], self.receiver.id)
        self.assertEqual(kwargs["notification_data"]["title"], "New Message")
        self.assertEqual(kwargs["notification_data"]["message"], f"New message from {self.sender.username}")
        self.assertEqual(kwargs["notification_data"]["notification_id"], str(notification.id))

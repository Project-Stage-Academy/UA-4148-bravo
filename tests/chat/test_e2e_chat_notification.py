import os
import json
import asyncio
from django.test import TestCase, override_settings
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from chat.consumers import NotificationConsumer
from chat.documents import Message, Room
from communications.models import Notification
from users.models import User, UserRole
from mongoengine import connect, disconnect
import mongomock

TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


@override_settings(CELERY_TASK_ALWAYS_EAGER=False)
class NotificationEndToEndTestCase(TestCase):
    """
    End-to-end test for notification system:
    Message -> Signal -> Celery Task -> WebSocket Notification
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
            role=role_startup
        )
        self.receiver = User.objects.create_user(
            email="receiver@example.com",
            password=TEST_USER_PASSWORD,
            first_name="Receiver",
            last_name="User",
            role=role_investor
        )

    async def async_connect_user(self, user):
        communicator = WebsocketCommunicator(NotificationConsumer.as_asgi(), "/ws/notifications/")
        communicator.scope["user"] = user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_notification_flow(self):
        """
        Full E2E test:
        1. Create Message
        2. Signal triggers Notification
        3. Celery task executes
        4. WebSocket receives notification
        """

        async def run_test():
            communicator = await self.async_connect_user(self.receiver)

            room = Room(name="chat_room", participants=[self.sender.email, self.receiver.email]).save()
            message = Message(room=room, sender_email=self.sender.email, receiver_email=self.receiver.email,
                              text="E2E test message")
            message.save()

            channel_layer = get_channel_layer()
            group_name = f"notifications_{self.receiver.id}"

            for _ in range(10):
                notifications = Notification.objects.filter(recipient=self.receiver)
                if notifications.exists():
                    break
                await asyncio.sleep(0.5)
            self.assertTrue(notifications.exists())
            notification = notifications.first()

            response = await communicator.receive_from(timeout=5)
            data = json.loads(response)
            self.assertIn("notification", data)
            self.assertEqual(data["notification"]["title"], "New Message")
            self.assertEqual(data["notification"]["message"], f"New message from {self.sender.username}")
            self.assertEqual(data["notification"]["notification_id"], str(notification.id))

            await communicator.disconnect()

        self.run_async(run_test())

import os
import json
import asyncio
from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from chat.routing import websocket_urlpatterns
from chat.documents import Message, Room
from communications.models import Notification
from tests.communications.factories import NotificationTypeFactory
from users.models import User, UserRole
from mongoengine import connect, disconnect
import mongomock
from unittest.mock import patch
from asgiref.sync import sync_to_async
from communications.tasks import send_notification_task

TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


class NotificationE2ETestCase(TransactionTestCase):
    """
    Stable end-to-end test for the notification flow:
    Message -> Signal/Task -> Notification -> WebSocket
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
        application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
        communicator = WebsocketCommunicator(application, "/ws/notifications/")
        communicator.scope["user"] = user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_notification_flow(self):
        async def run_test():
            communicator = await self.async_connect_user(self.receiver)

            with patch("chat.documents.get_user_or_raise") as mock_get_user:
                mock_get_user.side_effect = lambda email, room_name: {
                    self.sender.email: self.sender,
                    self.receiver.email: self.receiver
                }.get(email, None)

                room = Room(name="chat_room", participants=[self.sender.email, self.receiver.email])
                await sync_to_async(room.save)()

            message = Message(
                room=room,
                sender_email=self.sender.email,
                receiver_email=self.receiver.email,
                text="E2E test message"
            )
            await sync_to_async(message.save)()

            self.type_message = await sync_to_async(NotificationTypeFactory.create)(code='chat_message_new')

            notification = await sync_to_async(Notification.objects.create)(
                user=self.receiver,
                notification_type=self.type_message,
                title="New Message",
                message=f"New message from {self.sender.email}",
                related_message_id=str(message.id)
            )
            await sync_to_async(send_notification_task)(
                user_id=self.receiver.id,
                notification_data={
                    "title": "New Message",
                    "message": f"New message from {self.sender.email}",
                    "notification_id": str(notification.notification_id),
                }
            )

            max_retries = 40
            poll_interval = 0.25

            notification_fetched = None
            notification_data = None

            for _ in range(max_retries):
                notifications_qs = await sync_to_async(Notification.objects.filter)(user=self.receiver)
                exists = await sync_to_async(notifications_qs.exists)()
                if exists and notification_fetched is None:
                    notification_fetched = await sync_to_async(notifications_qs.first)()

                if notification_data is None:
                    try:
                        response = await communicator.receive_from(timeout=poll_interval)
                        notification_data = json.loads(response)
                    except asyncio.TimeoutError:
                        pass

                if notification_fetched and notification_data:
                    break

                await asyncio.sleep(poll_interval)

            self.assertIsNotNone(notification_data, "Notification was not received via WebSocket.")
            self.assertIn("notification", notification_data)
            self.assertEqual(notification_data["notification"]["title"], "New Message")
            self.assertEqual(
                notification_data["notification"]["message"],
                f"New message from {self.sender.email}"
            )
            self.assertEqual(
                notification_data["notification"]["notification_id"],
                str(notification_fetched.notification_id)
            )

            await communicator.disconnect()

        self.run_async(run_test())

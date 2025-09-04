import os
import json
from asgiref.sync import async_to_sync
from django.test import TestCase
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from chat.consumers import NotificationConsumer
from users.models import User, UserRole
from mongoengine import connect, disconnect
import mongomock

TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


class NotificationConsumerTestCase(TestCase):
    """
    Tests for the NotificationConsumer WebSocket consumer.
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

        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password=TEST_USER_PASSWORD,
            first_name="First",
            last_name="User",
            role=role_startup,
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password=TEST_USER_PASSWORD,
            first_name="Second",
            last_name="User",
            role=role_investor,
        )

    async def async_connect_user(self, user):
        """
        Helper function to create a WebSocket communicator and connect the user.
        """
        communicator = WebsocketCommunicator(NotificationConsumer.as_asgi(), "/ws/notifications/")
        communicator.scope["user"] = user
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    def run_async(self, coro):
        """Helper to run async tests inside Django's TestCase."""
        return async_to_sync(coro)

    def test_connect_and_disconnect(self):
        """Test that the consumer can connect and disconnect successfully."""

        async def run_test():
            communicator = await self.async_connect_user(self.user1)
            await communicator.disconnect()

        self.run_async(run_test())

    def test_send_notification(self):
        """Test that a notification sent to the user's group is received via WebSocket."""

        async def run_test():
            communicator = await self.async_connect_user(self.user1)
            channel_layer = get_channel_layer()
            group_name = f"notifications_{self.user1.id}"

            notification_data = {"title": "Hello", "message": "Test message"}
            await channel_layer.group_send(group_name, {
                "type": "send_notification",
                "notification": notification_data
            })

            response = await communicator.receive_from()
            response_data = json.loads(response)

            self.assertIn("notification", response_data)
            self.assertEqual(response_data["notification"], notification_data)

            await communicator.disconnect()

        self.run_async(run_test())

    def test_unauthenticated_user_rejected(self):
        """Test that unauthenticated users cannot connect."""

        async def run_test():
            communicator = WebsocketCommunicator(NotificationConsumer.as_asgi(), "/ws/notifications/")
            from django.contrib.auth.models import AnonymousUser
            communicator.scope["user"] = AnonymousUser()
            connected, _ = await communicator.connect()
            self.assertFalse(connected)

        self.run_async(run_test())

    def test_multiple_connections_same_user(self):
        """Test that multiple connections from the same user are supported."""

        async def run_test():
            comm1 = await self.async_connect_user(self.user1)
            comm2 = await self.async_connect_user(self.user1)

            channel_layer = get_channel_layer()
            group_name = f"notifications_{self.user1.id}"

            notification_data = {"title": "Ping", "message": "Multi-connection test"}
            await channel_layer.group_send(group_name, {
                "type": "send_notification",
                "notification": notification_data
            })

            resp1 = json.loads(await comm1.receive_from())
            resp2 = json.loads(await comm2.receive_from())

            self.assertEqual(resp1["notification"], notification_data)
            self.assertEqual(resp2["notification"], notification_data)

            await comm1.disconnect()
            await comm2.disconnect()

        self.run_async(run_test())

    def test_multiple_notifications(self):
        """Test that multiple notifications are received in order."""

        async def run_test():
            communicator = await self.async_connect_user(self.user1)
            channel_layer = get_channel_layer()
            group_name = f"notifications_{self.user1.id}"

            notifications = [
                {"title": "First", "message": "First message"},
                {"title": "Second", "message": "Second message"},
                {"title": "Third", "message": "Third message"},
            ]

            for note in notifications:
                await channel_layer.group_send(group_name, {
                    "type": "send_notification",
                    "notification": note
                })

            for expected in notifications:
                response = json.loads(await communicator.receive_from())
                self.assertEqual(response["notification"], expected)

            await communicator.disconnect()

        self.run_async(run_test())

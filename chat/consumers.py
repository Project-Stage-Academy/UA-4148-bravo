import json
import logging
import re
from typing import Optional, Tuple, Dict, Any
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from mongoengine import ValidationError, DoesNotExist
from chat.documents import Room, Message, MIN_MESSAGE_LENGTH, MAX_MESSAGE_LENGTH
from chat.permissions import check_user_in_room
from core.settings.constants import FORBIDDEN_WORDS_SET
from users.models import User, UserRole
from utils.messages_rate_limit import is_rate_limited
from utils.sanitize import sanitize_message
import sentry_sdk
from utils.save_documents import log_and_capture

logger = logging.getLogger(__name__)


class InvestorStartupMessageConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time messaging between investors and startups.

    Features:
        - Authenticates users and validates roles (Investor/Startup).
        - Creates or retrieves a chat room based on participants.
        - Broadcasts messages in a room group.
        - Validates messages for length, forbidden words, spam, and rate limits.
        - Persists messages in MongoDB using MongoEngine.

    Attributes:
        user (Optional[User]): Current WebSocket user.
        other_user (Optional[User]): The other participant in the chat.
        room (Optional[Room]): MongoDB Room object for the chat.
        room_group_name (Optional[str]): Channels group name for broadcasting messages.
    """
    user: Optional[User]
    other_user: Optional[User]
    room: Optional[Room]
    room_group_name: Optional[str]

    async def connect(self):
        """
        Handles WebSocket connection.

        Workflow:
            1. Checks user authentication.
            2. Retrieves the other user by email.
            3. Creates or fetches a chat room (investor-startup).
            4. Verifies that the user is a participant of the room.
            5. Joins the Channels group and accepts the connection.

        Closing codes:
            4401 → unauthenticated,
            4404 → not found,
            4403 → forbidden,
            1011 → internal error.
        """
        self.user = self.scope.get('user', None)
        other_user_email = self.scope["url_route"]["kwargs"].get("other_user_email")

        if not self.user or not self.user.is_authenticated:
            logger.warning("[CONNECT] Unauthenticated user")
            await self.close(code=4401)
            return

        self.other_user = await self.get_user_by_email(other_user_email)
        if not self.other_user:
            logger.warning("[CONNECT] Other user not found: %s", other_user_email)
            await self.close(code=4404)
            return

        try:
            self.room, created = await self.get_or_create_chat_room(self.user, self.other_user)
            logger.info("[CONNECT] Room %s, created=%s", self.room.name, created)
        except ValidationError as ve:
            logger.error("[CONNECT] Failed to create/get room: %s", ve)
            sentry_sdk.capture_exception(ve)
            await self.close(code=1011)
            return

        if not check_user_in_room(self.user, self.room):
            await self.close(code=4403)
            return

        self.room_group_name = f"chat_{self.room.id}"

        try:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            logger.info("[CONNECT] Connected to room group: %s", self.room_group_name)
        except Exception as e:
            logger.error("[CONNECT] Failed to add channel: %s", e)
            sentry_sdk.capture_exception(e)
            await self.close(code=1011)

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection.

        Removes the channel from the room group.
        """
        try:
            if hasattr(self, "room_group_name"):
                await self.channel_layer.group_discard(
                    self.room_group_name, self.channel_name
                )
            logger.info("[DISCONNECT] Left room: %s", self.room_group_name)
        except Exception as e:
            logger.error("[DISCONNECT] Failed to discard channel: %s", e)
            sentry_sdk.capture_exception(e)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handles incoming WebSocket messages.

        Validates message length, forbidden words, spam patterns, and rate limits.
        Persists the message and broadcasts it to the room group.

        Args:
            text_data (str): JSON-formatted message data.
            bytes_data (bytes): Not used.
        """
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()
            if not message:
                return
            message = sanitize_message(message)

            if len(message) < MIN_MESSAGE_LENGTH or len(message) > MAX_MESSAGE_LENGTH:
                await self.send(
                    json.dumps({"error": f"Message length must be {MIN_MESSAGE_LENGTH}-{MAX_MESSAGE_LENGTH} chars"}))
                return

            if any(word in message.lower() for word in FORBIDDEN_WORDS_SET):
                await self.send(json.dumps({"error": "Message contains forbidden content"}))
                logger.warning("[MESSAGE] Forbidden content by %s in room %s", self.user.email, self.room_group_name)
                return

            if re.match(r"(.)\1{10,}", message):
                await self.send(json.dumps({"error": "Message looks like spam"}))
                logger.warning("[MESSAGE] Spam detected by %s in room %s", self.user.email, self.room_group_name)
                sentry_sdk.capture_message(f"Spam detected from {self.user.email} in room {self.room_group_name}",
                                           level="warning")
                return

            if is_rate_limited(self.user.id, self.room_group_name):
                await self.send(json.dumps({"error": "Rate limit exceeded"}))
                return

            try:
                msg = await self.save_message(message)
                logger.info("[RECEIVE] Message saved from %s: %s", self.user.email, msg.text[:50])
            except ValidationError as ve:
                logger.error("[RECEIVE] Failed to save message: %s", ve)
                sentry_sdk.capture_exception(ve)
                await self.send(json.dumps({"error": "Failed to save message"}))
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "receive_chat_message",
                    "message": message,
                    "sender": self.user.email
                }
            )

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON: %s | %s", text_data, e)
            sentry_sdk.capture_exception(e)
        except Exception as e:
            logger.error("Error in receive: %s", e)
            sentry_sdk.capture_exception(e)

    async def receive_chat_message(self, event):
        """
        Handles messages received from the room group and sends them to the WebSocket client.

        This method is called by Channels when a message is broadcasted to the group.
        Logs sending activity for monitoring real-time communication.

        Args:
            event (dict): Contains 'message' (str) and 'sender' (str) keys.
        """
        message = event.get("message", "")
        sender = event.get("sender", "")

        try:
            await self.send(json.dumps({
                "message": message,
                "sender": sender
            }))
            logger.info("[SEND_MESSAGE] Sent message to %s in room %s: %s",
                        self.user.email if self.user else "UNKNOWN",
                        self.room_group_name,
                        message[:50] + ("..." if len(message) > 50 else ""))
        except Exception as e:
            logger.error("[receive_chat_message] Failed to send message: %s", e)
            sentry_sdk.capture_exception(e)

    @database_sync_to_async
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieves a User object by email.

        Args:
            email (str): Email of the user.

        Returns:
            Optional[User]: User instance or None if not found.
        """
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    @log_and_capture("room", ValidationError)
    def get_or_create_chat_room(self, user1, user2) -> Tuple[Room, bool]:
        """
        Creates or retrieves a chat room between an investor and a startup.
        """
        roles = {user1.role.role if user1.role else None, user2.role.role if user2.role else None}

        if roles != {UserRole.Role.STARTUP, UserRole.Role.INVESTOR}:
            raise ValidationError("Chat room must have exactly one Startup and one Investor.")

        startup = user1 if user1.role.role == UserRole.Role.STARTUP else user2
        investor = user2 if user2.role.role == UserRole.Role.INVESTOR else user1

        room_name = f"{startup.email}_{investor.email}"

        try:
            room = Room.objects.get(name=room_name)
            return room, False
        except DoesNotExist:
            room = Room(name=room_name, participants=[startup.email, investor.email])
            room.save()
            return room, True

    @database_sync_to_async
    @log_and_capture("message", ValidationError)
    def save_message(self, message_text: str) -> Message:
        """
        Saves a message to the Room in MongoDB.

        Adds missing participants to the room if necessary.

        Args:
            message_text (str): The text of the message.

        Returns:
            Message: The saved Message instance.
        """
        sender_email = self.user.email
        receiver_email = self.other_user.email if self.other_user else None

        updated = False
        for email in [sender_email, receiver_email]:
            if email and email not in self.room.participants:
                self.room.participants.append(email)
                updated = True
        if updated:
            self.room.save()

        msg = Message(room=self.room,
                      sender_email=sender_email,
                      receiver_email=receiver_email,
                      text=message_text)
        msg.save()
        return msg


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for sending real-time notifications to authenticated users.

    Each user has their own notification group identified by their user ID.
    """

    async def connect(self) -> None:
        """
        Called when a WebSocket connection is opened.

        Joins the user's notification group and accepts the connection.
        """
        user = self.scope["user"]

        if not user.is_authenticated:
            logger.warning("[NOTIFICATION_WS] Unauthorized connection attempt")
            await self.close()
            return

        self.room_group_name: str = f'notifications_{user.id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        logger.info("[NOTIFICATION_WS] User %s connected to %s", user.email, self.room_group_name)

    async def disconnect(self, close_code: int) -> None:
        """
        Called when the WebSocket connection is closed.

        Leaves the user's notification group.

        Args:
            close_code (int): WebSocket close code.
        """
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
        logger.info("[NOTIFICATION_WS] User %s disconnected (code=%s)", self.scope["user"].email, close_code)

    async def send_notification(self, event: Dict[str, Any]) -> None:
        """
        Receive a notification event from the channel layer and send it to the WebSocket.

        Args:
            event (dict): Event data containing the 'notification' key.
        """
        notification: Dict[str, Any] = event["notification"]

        await self.send(text_data=json.dumps({
            'notification': notification
        }))
        logger.debug("[NOTIFICATION_WS] Sent notification to %s | data=%s",
                     self.scope["user"].email, notification)

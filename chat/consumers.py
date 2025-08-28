import json
import logging
import os
import re
import time
from collections import defaultdict
from typing import Optional, Tuple
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from mongoengine import ValidationError, DoesNotExist
from chat.documents import Room, Message
from core.settings.constants import FORBIDDEN_WORDS_SET
from users.models import User
from utils.sanitize import sanitize_message

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 1000))
MIN_MESSAGE_LENGTH = int(os.getenv("MIN_MESSAGE_LENGTH", 1))
MESSAGE_RATE_LIMIT = int(os.getenv("MESSAGE_RATE_LIMIT", 5))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 10))

user_message_times = defaultdict(list)


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
            4. Joins the Channels group and accepts the connection.
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
            await self.close(code=1011)
            return

        self.room_group_name = f"chat_{self.room.id}"

        try:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            logger.info("[CONNECT] Connected to room group: %s", self.room_group_name)
        except Exception as e:
            logger.error("[CONNECT] Failed to add channel: %s", e)
            await self.close(code=1011)

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection.

        Removes the channel from the room group.
        """
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            logger.info("[DISCONNECT] Left room: %s", self.room_group_name)
        except Exception as e:
            logger.error("[DISCONNECT] Failed to discard channel: %s", e)

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
                return
            if re.match(r"(.)\1{10,}", message):
                await self.send(json.dumps({"error": "Message looks like spam"}))
                return

            now = time.time()
            times = user_message_times[self.channel_name]
            times = [t for t in times if now - t < RATE_LIMIT_WINDOW]
            times.append(now)
            user_message_times[self.channel_name] = times
            if len(times) > MESSAGE_RATE_LIMIT:
                await self.send(json.dumps({"error": "Rate limit exceeded"}))
                return

            try:
                msg = await self.save_message(message)
                logger.info("[RECEIVE] Message saved from %s: %s", self.user.email, msg.text[:50])
            except ValidationError as ve:
                logger.error("[RECEIVE] Failed to save message: %s", ve)
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
        except Exception as e:
            logger.error("Error in receive: %s", e)

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
    def get_or_create_chat_room(self, user1, user2) -> Tuple[Room, bool]:
        """
        Creates or retrieves a chat room between an investor and a startup.

        Args:
            user1 (User): One participant.
            user2 (User): Another participant.

        Returns:
            Tuple[Room, bool]: The Room instance and a boolean indicating if it was created.
        """
        investor = user1 if hasattr(user1, 'roles') and user1.roles.filter(name='Investor').exists() else user2
        startup = user2 if hasattr(user2, 'roles') and user2.roles.filter(name='Startup').exists() else user1

        room_name = f"{investor.email}_{startup.email}"

        try:
            room = Room.objects.get(name=room_name)
            created = False
        except DoesNotExist:
            room = Room(name=room_name, participants=[investor.email, startup.email])
            try:
                room.save()
                created = True
            except ValidationError as ve:
                logger.error("[get_or_create_chat_room] Failed to save room: %s", ve)
                raise ve

        return room, created

    @database_sync_to_async
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
            try:
                self.room.save()
                logger.info("[SAVE_MESSAGE] Updated participants for room: %s", self.room.name)
            except ValidationError as ve:
                logger.error("[SAVE_MESSAGE] Failed to update room participants: %s", ve)
                raise ve

        msg = Message(room=self.room, sender_email=sender_email, receiver_email=receiver_email, text=message_text)
        try:
            msg.save()
            logger.info("[SAVE_MESSAGE] Saved message in room '%s'", self.room.name)
        except ValidationError as ve:
            logger.error("[SAVE_MESSAGE] Failed to save message: %s", ve)
            raise ve

        return msg

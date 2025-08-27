import json
import logging
import os
import re
import time
from collections import defaultdict
from channels.generic.websocket import AsyncWebsocketConsumer
from mongoengine import ValidationError
from channels.db import database_sync_to_async
from chat.documents import Room, Message
from core.settings.constants import FORBIDDEN_WORDS_SET
from django.contrib.auth import get_user_model
from mongoengine import DoesNotExist
from typing import Tuple, Optional

from users.models import User

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 1000))
MIN_MESSAGE_LENGTH = int(os.getenv("MIN_MESSAGE_LENGTH", 1))
MESSAGE_RATE_LIMIT = int(os.getenv("MESSAGE_RATE_LIMIT", 5))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 10))

user_message_times = defaultdict(list)


class InvestorStartupMessageConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time messaging between investors and startups.

    This consumer enables:
      - Joining specific messaging rooms (e.g., based on user pairs or startup profiles).
      - Broadcasting messages to all members of a room.
      - Sending/receiving messages via WebSocket in real-time.

    Attributes:
        user (Optional[User]): Current user connected to the WebSocket.
        other_user (Optional[User]): The other participant in the chat.
        room (Optional[Room]): The database Room object for this chat.
        room_name (Optional[str]): Identifier for the messaging room, extracted from the WebSocket URL.
        room_group_name (Optional[str]): Group name used by Channels to broadcast messages.
    """
    user: Optional[User]
    other_user: Optional[User]
    room: Optional[Room]
    room_name: Optional[str]
    room_group_name: Optional[str]

    def __init__(self, *args, **kwargs):
        """ Initialize the WebSocket consumer with default attributes. """
        super().__init__(*args, **kwargs)
        self.user: Optional[User] = None
        self.other_user: Optional[User] = None
        self.room: Optional[Room] = None
        self.room_name: Optional[str] = None
        self.room_group_name: Optional[str] = None

    async def connect(self) -> None:
        """
        Handles a new WebSocket connection between two users.

        Workflow:
        1. Validates that the current user (`self.user`) is authenticated.
        2. Retrieves the `other_user` from the URL and validates their existence.
        3. Creates or retrieves a chat room object (MongoEngine-backed).
        4. Sanitizes the `room_name` from the URL to allow only alphanumeric,
           dash (-), and underscore (_), and truncates to 50 characters max.
        5. Adds the WebSocket channel to the appropriate group.
        6. Accepts the connection if all checks pass.

        Custom WebSocket close codes used:
        - 4401 → Unauthorized: the connecting user is not authenticated.
        - 4404 → Not Found: the other user with the provided ID does not exist.
        - 4000 → Invalid room name: the `room_name` contains only invalid characters.
        - 1011 → Internal Error: failed to add channel to group (unexpected error).
        """
        self.user = self.scope.get('user', None)
        other_user_id = self.scope['url_route']['kwargs'].get('other_user_id')

        if not self.user or not self.user.is_authenticated:
            logger.warning("Unauthenticated user tried to connect")
            await self.close(code=4401)
            return

        self.other_user = await self.get_user_by_id(other_user_id)
        if not self.other_user:
            logger.warning("Invalid other_user_id: %s", other_user_id)
            await self.close(code=4404)
            return

        room, created = await self.get_or_create_chat_room(self.user, self.other_user)
        self.room = room

        raw_room_name = self.scope["url_route"]["kwargs"]["room_name"]

        safe_room_name = re.sub(r"[^a-zA-Z0-9_-]", "", raw_room_name)[:50]

        if not safe_room_name:
            logger.warning("Invalid room_name received: %s", raw_room_name)
            await self.close(code=4000)
            return

        self.room_name = safe_room_name
        self.room_group_name = f"chat_{self.room_name}"

        try:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            logger.info("Client connected to room: %s", self.room_group_name)
        except Exception as e:
            logger.error("Error adding channel to group %s: %s", self.room_group_name, e)
            await self.close(code=1011)

    @database_sync_to_async
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """ Sync ORM call wrapped to async. """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_or_create_chat_room(self, user1, user2) -> Tuple[Room, bool]:
        """
        Creates or retrieves a chat room between two users (MongoEngine version).
        Since MongoEngine has no get_or_create, we implement it manually.
        """
        if hasattr(user1, 'roles') and user1.roles.filter(name='Investor').exists():
            investor = user1
        else:
            investor = user2
        if hasattr(user1, 'roles') and user1.roles.filter(name='Startup').exists():
            startup = user2
        else:
            startup = user1

        try:
            room = Room.objects.get(name=f"{investor.id}_{startup.id}")
            created = False
        except DoesNotExist:
            room = Room(
                name=f"{investor.id}_{startup.id}",
                participants=[investor, startup]
            )
            room.save()
            created = True

        return room, created

    async def disconnect(self, close_code: int) -> None:
        """
        Handles WebSocket disconnection.
        Removes the connection from the room group.
        """
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            logger.info("Client disconnected from room: %s", self.room_group_name)
        except Exception as e:
            logger.error("Error removing channel from group %s: %s", self.room_group_name, e)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handles incoming messages from the WebSocket client.
        Validates size, rate, and content before broadcasting.
        """
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get("message")

            if not message or not isinstance(message, str):
                logger.warning("Invalid payload (missing/invalid 'message'): %s", text_data)
                return

            message = message.strip()

            if len(message) < MIN_MESSAGE_LENGTH or len(message) > MAX_MESSAGE_LENGTH:
                await self.send(text_data=json.dumps({
                    "error": f"Message must be between {MIN_MESSAGE_LENGTH} and {MAX_MESSAGE_LENGTH} characters."
                }))
                return

            lowered = message.lower()
            if any(word in lowered for word in FORBIDDEN_WORDS_SET):
                logger.warning("Blocked forbidden content: %s", message)
                await self.send(text_data=json.dumps({"error": "Message contains forbidden content."}))
                return

            if re.match(r"(.)\1{10,}", message):
                logger.warning("Blocked spammy message: %s", message)
                await self.send(text_data=json.dumps({"error": "Message looks like spam."}))
                return

            now = time.time()
            times = user_message_times[self.channel_name]
            times = [t for t in times if now - t < RATE_LIMIT_WINDOW]
            times.append(now)
            user_message_times[self.channel_name] = times

            if len(times) > MESSAGE_RATE_LIMIT:
                logger.warning("Rate limit exceeded by %s", self.channel_name)
                await self.send(text_data=json.dumps({"error": "Too many messages, slow down."}))
                return

            await self.save_message(self.room_name, str(self.user.id), str(self.other_user.id), message)
            logger.info("Message saved in room %s", self.room_name)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'receive_chat_message',
                    'message': message,
                    'sender': self.user.email,
                }
            )

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON received: %s | Error: %s", text_data, e)
        except Exception as e:
            logger.error("Error processing received message: %s", e)

    async def receive_chat_message(self, event: dict) -> None:
        """
        Handles messages received from the room group.
        Sends the message to the WebSocket client.
        """
        try:
            message = event.get("message", "")
            sender = event.get("sender", "")

            if not isinstance(message, str) or not message.strip():
                logger.warning("Received invalid or empty message in event: %s", event)
                return

            message = message.strip()

            await self.send(text_data=json.dumps({
                'message': message,
                'sender': sender,
            }))

        except Exception as e:
            logger.error("Error sending message to WebSocket client: %s", e)

    @database_sync_to_async
    def save_message(
            self, room_name: str, sender_id: str, receiver_id: Optional[str], message: str
    ) -> Message:
        """
        Save a chat message in MongoDB with proper room and participant handling.

        Steps:
        1. Rejects anonymous users and logs a warning.
        2. Retrieves the Room by `room_name` or creates it if it doesn't exist.
        3. Ensures the sender ID is a participant of the room.
        4. Creates and saves a Message object linked to the room.
        5. Logs actions for auditability, truncating long messages for readability.

        Notes:
        - `receiver_id` can be None for group messages.
        - Race conditions can occur if multiple requests create the same room; consider using upsert or transactions.
        """
        user = self.scope["user"]
        if not user:
            logger.warning("Anonymous user attempted to send message: %s", message)
            raise ValueError("Anonymous users cannot send messages")

        try:
            room = Room.objects.get(name=room_name)
            created = False
        except DoesNotExist:
            room = Room(name=room_name, participants=[str(sender_id)])
            room.save()
            created = True

        if not created:
            if str(sender_id) not in room.participants:
                room.participants.append(str(sender_id))
                try:
                    room.save()
                    logger.info("Added user %s to existing room '%s'", sender_id, room_name)
                except ValidationError as ve:
                    logger.error("Adding user to room failed: %s", ve)
                    raise ve

        msg = Message(
            room=room,
            sender_id=str(sender_id),
            receiver_id = str(receiver_id) if receiver_id is not None else None,
            text=message
        )
        try:
            msg.save()
            logger.info(
                "Saved message in room '%s' from user %s to user %s: %s",
                room_name, sender_id, receiver_id or "ALL",
                                      message[:50] + ("..." if len(message) > 50 else "")
            )
        except ValidationError as ve:
            logger.warning("Failed to save message: %s", ve)
            raise ve

        return msg

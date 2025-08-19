import json
import logging
import os
import re
import time
from collections import defaultdict
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from core.settings import FORBIDDEN_WORDS_SET
from chat.documents import Room, Message
from users.documents import UserDocument
from mongoengine import ValidationError

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
        room_name (Optional[str]): Identifier for the messaging room, extracted from the WebSocket URL.
        room_group_name (Optional[str]): Group name used by Channels to broadcast messages.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.room_name: str | None = None
        self.room_group_name: str | None = None

    async def connect(self):
        """
        Handle a new WebSocket connection.

        This method performs the following steps:
          1. Extracts the currently authenticated user from `self.scope`.
          2. Validates the user is authenticated.
          3. Joins the corresponding room group based on a sanitized room name
             (allowing only alphanumeric characters, dashes, and underscores).

        If the user is not authenticated, the connection is immediately closed
        with a custom close code.

        Close Codes:
            4001 (UNAUTHORIZED_CLOSE_CODE): Unauthorized connection attempt – the user is not authenticated.
            4000: Invalid room name.
            1011: Internal server error.
        """
        user = self.scope["user"]
        if not user or not user.is_authenticated:
            await self.close(code=4001)  # custom code
            return

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

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection.
        Removes the connection from the room group.
        """
        if self.room_group_name:
            try:
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                logger.info("Client disconnected from room: %s", self.room_group_name)
            except Exception as e:
                logger.error("Error removing channel from group %s: %s", self.room_group_name, e)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming WebSocket messages from clients.

        Steps:
          1. Validates that the incoming message exists and is a string.
          2. Enforces length constraints and blocks forbidden words or spam patterns.
          3. Applies rate limiting per user/channel.
          4. Retrieves the authenticated MongoDB user.
          5. Saves the message to the database with detailed logging.
          6. Broadcasts the message to the room group.

        Logs errors and audit information if user lookup or message saving fails.

        Args:
            text_data (str | None): JSON string containing the message payload.
            bytes_data (bytes | None): Not used (for binary messages).
        """
        try:
            if not text_data:
                return

            try:
                payload = json.loads(text_data)
            except json.JSONDecodeError as e:
                logger.error("Invalid JSON received in room %s by %s: %s | Error: %s",
                             self.room_name, self.channel_name, text_data, e)
                return

            message = payload.get("message")
            if not message or not isinstance(message, str):
                logger.warning("Invalid payload (missing/invalid 'message') in room %s by %s: %s",
                               self.room_name, self.channel_name, text_data)
                return

            message = message.strip()
            if len(message) < MIN_MESSAGE_LENGTH or len(message) > MAX_MESSAGE_LENGTH:
                await self.send(text_data=json.dumps({
                    "error": f"Message must be between {MIN_MESSAGE_LENGTH} and {MAX_MESSAGE_LENGTH} characters."
                }))
                return

            lowered = message.lower()
            if any(word in lowered for word in FORBIDDEN_WORDS_SET):
                logger.warning("Blocked forbidden content in room %s by %s: %s",
                               self.room_name, self.channel_name, message)
                await self.send(text_data=json.dumps({"error": "Message contains forbidden content."}))
                return

            if re.search(r"([^aeiou\s])\1{10,}", message, re.IGNORECASE):
                logger.warning(
                    "Blocked spammy message in room %s by %s: %s",
                    self.room_name,
                    self.channel_name,
                    message[:50] + ("..." if len(message) > 50 else "")
                )
                await self.send(text_data=json.dumps({"error": "Message looks like spam."}))
                return

            now = time.time()
            times = user_message_times[self.channel_name]
            times = [t for t in times if now - t < RATE_LIMIT_WINDOW]
            times.append(now)
            user_message_times[self.channel_name] = times

            if len(times) > MESSAGE_RATE_LIMIT:
                logger.warning("Rate limit exceeded in room %s by %s", self.room_name, self.channel_name)
                await self.send(text_data=json.dumps({"error": "Too many messages, slow down."}))
                return

            user_email = getattr(self.scope.get("user"), "email", None)
            if not user_email:
                logger.warning("Unauthenticated user attempted to send message in room %s: %s",
                               self.room_name, message)
                await self.send(text_data=json.dumps({"error": "Authentication required."}))
                return

            user = await self.get_mongo_user(user_email)
            if not user:
                logger.warning("MongoDB user not found for email %s in room %s. Message not saved: %s",
                               user_email, self.room_name, message)
                await self.send(text_data=json.dumps({"error": "User not found in MongoDB."}))
                return

            try:
                await self.save_message(self.room_name, user, message)
                logger.info("Message saved in room %s by %s: %s",
                            self.room_name, user_email, message[:50] + ("..." if len(message) > 50 else ""))
            except Exception as e:
                logger.error("Failed to save message in room %s by %s: %s | Error: %s",
                             self.room_name, user_email, message, e)
                await self.send(text_data=json.dumps({"error": "Failed to save message."}))
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "receive_chat_message", "message": message}
            )

        except Exception as e:
            logger.error("Unexpected error processing message in room %s by %s: %s",
                         self.room_name, self.channel_name, e)

    async def receive_chat_message(self, event):
        """
        Handles messages received from the room group.
        Sends the message to the WebSocket client.
        """
        try:
            message = event.get("message", "")

            if not isinstance(message, str) or not message.strip():
                logger.warning("Received invalid or empty message in event: %s", event)
                return

            message = message.strip()

            await self.send(text_data=json.dumps({"message": message}))

        except Exception as e:
            logger.error("Error sending message to WebSocket client: %s", e)

    @database_sync_to_async
    def get_mongo_user(self, email: str):
        """
        Retrieve a user document from MongoDB by email.

        This method runs in a thread-safe manner using `database_sync_to_async`,
        making it safe to call inside asynchronous consumers.

        Args:
            email (str): The email address of the user to look up.

        Returns:
            UserDocument | None: The corresponding user document if found,
            otherwise `None`.
        """
        try:
            return UserDocument.objects.get(email=email)
        except UserDocument.DoesNotExist:
            logger.warning("MongoEngine UserDocument not found for email: %s", email)
            return None

    @database_sync_to_async
    def save_message(self, room_name: str, user: UserDocument, message: str):
        """
        Save a chat message in MongoDB with proper room and participant handling.

        Steps:
        1. Rejects anonymous users and logs a warning.
        2. Retrieves the Room by `room_name` or creates it if it doesn't exist.
           Uses MongoEngine upsert to reduce race conditions.
        3. Ensures the user is a participant of the room.
           For large participant lists, consider using a set or indexed field for efficiency.
        4. Creates and saves a Message object linked to the room and user.
        5. Logs all actions for auditability, truncating long messages for readability.

        Notes:
        - Multiple parallel requests creating the same room could cause race conditions.
          Upsert or MongoDB transactions help prevent duplicates.
        - Ensure Room and Message models’ required fields and signals (timestamps, hooks) are respected.

        Args:
            room_name (str): The name of the chat room.
            user (UserDocument): The sender of the message.
            message (str): The text content of the message.

        Returns:
            Message: The saved Message object.

        Raises:
            ValueError: If the user is anonymous.
            ValidationError: If saving the room or message fails.
        """
        if not user:
            logger.warning("Anonymous user attempted to send message: %s", message)
            raise ValueError("Anonymous users cannot send messages")

        room, created = Room.objects.get_or_create(name=room_name)

        if created:
            room.participants = [user]
            try:
                room.save()
                logger.info("Created new room '%s' and added user %s", room_name, user.email)
            except ValidationError as ve:
                logger.error("Room creation failed: %s", ve)
                raise ve
        else:
            participant_ids = {u.id for u in room.participants}
            if user.id not in participant_ids:
                room.participants.append(user)
                try:
                    room.save()
                    logger.info("Added user %s to existing room '%s'", user.email, room_name)
                except ValidationError as ve:
                    logger.error("Adding user to room failed: %s", ve)
                    raise ve

        msg = Message(room=room, sender=user, text=message)
        try:
            msg.save()
            logger.info(
                "Saved message in room '%s' from user %s: %s",
                room_name,
                user.email,
                message[:50] + ("..." if len(message) > 50 else "")
            )
        except ValidationError as ve:
            logger.warning("Failed to save message: %s", ve)
            raise ve

        return msg

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
        room_name (str): Identifier for the messaging room, extracted from the WebSocket URL.
        room_group_name (str): Group name used by Channels to broadcast messages.
    """

    async def connect(self):
        """
        Handles a new WebSocket connection.
        Joins the corresponding room group based on a sanitized room name.
        It allows only alphanumeric, dash, underscore.
        """
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
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            logger.info("Client disconnected from room: %s", self.room_group_name)
        except Exception as e:
            logger.error("Error removing channel from group %s: %s", self.room_group_name, e)

    async def receive(self, text_data):
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

            self.save_message(self.room_name, message)
            logger.info("Message saved in room %s", self.room_name)

            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "receive_chat_message", "message": message}
            )

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON received: %s | Error: %s", text_data, e)
        except Exception as e:
            logger.error("Error processing received message: %s", e)

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
    def save_message(self, room_name: str, message: str):
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
        """
        user = self.scope["user"]
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
                user,
                message[:50] + ("..." if len(message) > 50 else "")
            )
        except ValidationError as ve:
            logger.warning("Failed to save message: %s", ve)
            raise ve

        return msg

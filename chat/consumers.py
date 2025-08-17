import json
import logging
import os
import re
import time
from collections import defaultdict
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

FORBIDDEN_WORDS = {
    "spam", "scam", "xxx", "viagra", "free money", "lottery", "bitcoin",
    "crypto", "click here", "subscribe", "buy now", "offer", "promotion",
    "gamble", "casino", "adult", "nsfw", "sex", "porn", "nude"
}
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
            if any(word in lowered for word in FORBIDDEN_WORDS):
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

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat messages in specific rooms.
    """

    async def connect(self):
        """
        Handles a new WebSocket connection.
        Joins the corresponding room group based on the room name.
        """
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """
        Handles WebSocket disconnection.
        Removes the connection from the room group.
        """
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Handles incoming messages from the WebSocket client.
        Broadcasts the message to all members of the room group.
        """
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    async def chat_message(self, event):
        """
        Handles messages received from the room group.
        Sends the message to the WebSocket client.
        """
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))

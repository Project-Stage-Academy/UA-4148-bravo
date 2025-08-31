from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from chat.documents import Room, Message
from users.cookie_jwt import CookieJWTAuthentication
from users.views.base_protected_view import CookieJWTProtectedView
from chat.serializers import RoomSerializer, MessageSerializer
from rest_framework.pagination import LimitOffsetPagination


class ConversationCreateView(generics.CreateAPIView):
    """
    Create a new conversation (Room).

    Endpoint:
        POST /api/conversations/

    Request body example:
        {
            "name": "friends_group",
            "is_group": true,
            "participants": ["user1", "user2", "user3"]
        }

    Response example:
        {
            "name": "friends_group",
            "is_group": true,
            "participants": ["user1", "user2", "user3"]
        }
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = RoomSerializer


class SendMessageView(CookieJWTProtectedView):
    """
    Send a new message within a conversation and broadcast it via WebSocket.

    Endpoint:
        POST /api/messages/

    Request body example:
        {
            "room": "friends_group",
            "sender_id": "user1",
            "text": "Hello everyone!"
        }

    Response example:
        {
            "room": "friends_group",
            "sender_id": "user1",
            "receiver_id": null,
            "text": "Hello everyone!",
            "timestamp": "2025-08-25T20:00:00Z",
            "is_read": false
        }
    """

    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            message = serializer.save()
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        channel_layer = get_channel_layer()
        room_name = message.room.name
        data = MessageSerializer(message).data

        async_to_sync(channel_layer.group_send)(
            f"chat_{room_name}",
            {"type": "chat_message", "message": data}
        )

        return Response(data, status=status.HTTP_201_CREATED)


class ConversationMessagesView(generics.ListAPIView):
    """
    Retrieve the list of messages in a conversation.

    Endpoint:
        GET /api/conversations/{room_name}/messages/

    Path parameter:
        room_name (str): Name of the conversation/room.

    Response example:
        [
            {
                "room": "friends_group",
                "sender_id": "user1",
                "receiver_id": null,
                "text": "Hello everyone!",
                "timestamp": "2025-08-25T20:00:00Z",
                "is_read": false
            },
            {
                "room": "friends_group",
                "sender_id": "user2",
                "receiver_id": "user1",
                "text": "Hi!",
                "timestamp": "2025-08-25T20:01:00Z",
                "is_read": false
            }
        ]
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        room_name = self.kwargs["room_name"]
        room = get_object_or_404(Room, name=room_name)
        return Message.objects.filter(room=room).order_by("timestamp")

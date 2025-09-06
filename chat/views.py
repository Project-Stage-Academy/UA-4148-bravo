import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http.response import Http404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from chat.documents import Room, Message
from chat.permissions import IsOwnerOrRecipient
from rest_framework.views import APIView
from users.cookie_jwt import CookieJWTAuthentication
from chat.serializers import RoomSerializer, MessageSerializer
from rest_framework.pagination import LimitOffsetPagination
from mongoengine.errors import ValidationError as MongoValidationError
import sentry_sdk
from rest_framework.exceptions import ValidationError as DRFValidationError
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers

from users.permissions import HasActiveCompanyAccount, IsAuthenticatedOr401

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Chat"],
    summary="Create a new private conversation (Room)",
    description=(
            "Creates a private Room between exactly 2 participants: one Investor and one Startup. "
            "Returns Room details with timestamps. Validation ensures exactly 2 participants."
    ),
    request=RoomSerializer,
    responses={
        201: OpenApiResponse(
            description="Room created successfully",
            response=RoomSerializer,
        ),
        400: OpenApiResponse(
            description="Invalid input or room creation failed",
            response=inline_serializer(
                name="RoomCreateErrorResponse",
                fields={"error": serializers.CharField()},
            ),
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided",
            response=inline_serializer(
                name="UnauthorizedResponse",
                fields={"detail": serializers.CharField()},
            ),
        ),
    },
)
class ConversationCreateView(generics.CreateAPIView):
    """
    Create a new private conversation (Room) between exactly 2 participants:
    one Investor and one Startup.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedOr401, HasActiveCompanyAccount]
    serializer_class = RoomSerializer

    def perform_create(self, serializer):
        """Enforce exactly 2 participants for private chat."""
        participants = serializer.validated_data.get("participants", [])
        if len(participants) != 2:
            msg = "Private room must have exactly 2 participants."
            logger.warning("[ROOM_CREATE] %s | participants=%s", msg, participants)
            sentry_sdk.capture_message(msg, level="warning")
            raise DRFValidationError({"error": msg})
        return serializer.save()

    def create(self, request, *args, **kwargs):
        """Override to return serialized Room with timestamps in response."""
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            if Room.objects(name=serializer.validated_data["name"]).first():
                msg = "Room name already exists."
                logger.warning("[ROOM_CREATE] %s | data=%s", msg, request.data)
                sentry_sdk.capture_message(msg, level="warning")
                return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)

            room = self.perform_create(serializer)
            logger.info("[ROOM_CREATE] Created room: %s | participants=%s", room.name, room.participants)
        except DRFValidationError as e:
            logger.warning("[ROOM_CREATE] Validation failed: %s | data=%s", e, request.data)
            sentry_sdk.capture_exception(e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except MongoValidationError as e:
            logger.warning("[ROOM_CREATE] Mongo validation failed: %s | data=%s", e, request.data)
            sentry_sdk.capture_exception(e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("[ROOM_CREATE] Unexpected error: %s | data=%s", e, request.data)
            sentry_sdk.capture_exception(e)
            return Response({'error': 'Unexpected error: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        headers = self.get_success_headers(serializer.data)
        return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema(
    tags=["Chat"],
    summary="Send a new private message",
    description=(
            "Sends a message inside a private Room between 2 participants. "
            "If the Room does not exist, it is automatically created. "
    ),
    request=MessageSerializer,
    responses={
        201: OpenApiResponse(
            description="Message sent successfully",
            response=MessageSerializer,
        ),
        400: OpenApiResponse(
            description="Invalid message data or room creation failed",
            response=inline_serializer(
                name="MessageSendErrorResponse",
                fields={"error": serializers.CharField()},
            ),
        ),
        403: OpenApiResponse(
            description="Sender is not a participant of the Room",
            response=inline_serializer(
                name="MessageSendForbiddenResponse",
                fields={"error": serializers.CharField()},
            ),
        ),
        500: OpenApiResponse(
            description="Unexpected server error while saving message",
            response=inline_serializer(
                name="MessageSendServerErrorResponse",
                fields={"error": serializers.CharField()},
            ),
        ),
    },
)
class SendMessageView(APIView):
    """
    Send a new message within a conversation.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedOr401, IsOwnerOrRecipient, HasActiveCompanyAccount]
    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data, context={"sender_email": request.user.email})
        try:
            serializer.is_valid(raise_exception=True)
        except DRFValidationError as e:
            logger.warning("[MESSAGE_SEND] Validation failed: %s | data=%s", e, request.data)
            sentry_sdk.capture_message(f"Message validation failed: {e}", level="warning")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        room_name = serializer.validated_data["room_name"]
        sender_email = request.user.email
        receiver_email = serializer.validated_data["receiver_email"]

        room = Room.objects(name=room_name).first()
        if not room:
            if len({sender_email, receiver_email}) != 2:
                msg = "Private room must have exactly 2 participants."
                logger.warning("[MESSAGE_SEND] %s | sender=%s receiver=%s", msg, sender_email, receiver_email)
                sentry_sdk.capture_message(msg, level="warning")
                return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)

            room = Room(name=room_name, participants=[sender_email, receiver_email])
            try:
                room.save()
                logger.info("[ROOM_CREATE] Auto-created room: %s | participants=%s", room.name, room.participants)
            except Exception as e:
                logger.error("[ROOM_CREATE] Failed to auto-create room: %s | error=%s", room_name, e)
                sentry_sdk.capture_exception(e)
                return Response({'error': f"Failed to create room: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if sender_email not in room.participants:
            msg = "You are not a participant of this room."
            logger.warning("[MESSAGE_SEND] Forbidden sender=%s room=%s", sender_email, room_name)
            sentry_sdk.capture_message(msg, level="warning")
            return Response({"error": msg}, status=status.HTTP_403_FORBIDDEN)

        try:
            message = serializer.save()
            logger.info(
                "[MESSAGE_SEND] Sent message | sender=%s receiver=%s room=%s text_preview=%s",
                sender_email, receiver_email, room_name,
                message.text[:50] + ("..." if len(message.text) > 50 else "")
            )
        except Exception as e:
            logger.error("[MESSAGE_SEND] Failed to save message | sender=%s receiver=%s room=%s error=%s",
                         sender_email, receiver_email, room_name, e)
            sentry_sdk.capture_exception(e)
            return Response({'error': f"Failed to save message: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{room_name}",
            {"type": "chat_message", "message": MessageSerializer(message).data}
        )

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Chat"],
    summary="List messages in a conversation",
    description=(
            "Retrieves all messages from a specific Room that the authenticated user participates in. "
            "Returns messages ordered by timestamp."
    ),
    responses={
        200: OpenApiResponse(
            description="List of messages",
            response=MessageSerializer(many=True),
        ),
        401: OpenApiResponse(
            description="Authentication credentials were not provided",
            response=inline_serializer(
                name="UnauthorizedResponse",
                fields={"detail": serializers.CharField()},
            ),
        ),
        404: OpenApiResponse(
            description="Room does not exist or user is not a participant",
            response=inline_serializer(
                name="RoomNotFoundResponse",
                fields={"detail": serializers.CharField()},
            ),
        ),
    },
)
class ConversationMessagesView(generics.ListAPIView):
    """
    Retrieve messages for a conversation by room_name.
    Only participants can access.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOrRecipient, HasActiveCompanyAccount]
    serializer_class = MessageSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        room_name = self.kwargs.get("room_name")
        user_email = getattr(self.request.user, "email", None)

        room = Room.objects(name=room_name).first()
        if not room:
            msg = f"Room '{room_name}' does not exist"
            logger.warning("[MESSAGES_FETCH] %s", msg)
            sentry_sdk.capture_message(msg, level="warning")
            raise Http404(msg)

        if user_email not in room.participants:
            msg = f"Access denied to Room '{room_name}'"
            logger.warning("[MESSAGES_FETCH] %s | user=%s", msg, user_email)
            sentry_sdk.capture_message(msg, level="warning")
            raise Http404(msg)

        return Message.objects(
            room=room,
            __raw__={"$or": [{"sender_email": user_email}, {"receiver_email": user_email}]}
        ).order_by("timestamp")

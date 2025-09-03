import logging
from django.core.management.base import BaseCommand
from mongoengine.errors import ValidationError
from chat.documents import Message
from users.models import User, UserRole
from utils.chat_utils import get_or_create_room
from utils.encrypt import encrypt_string
from utils.save_documents import log_and_capture

logger = logging.getLogger(__name__)

TEST_USERS = [
    {"email": "user1@example.com", "role": "user"},
    {"email": "user2@example.com", "role": "user"},
    {"email": "investor@example.com", "role": "investor"},
    {"email": "startup@example.com", "role": "startup"},
]

TEST_MESSAGES = [
    "Hello! This is a test message.",
    "How are you today?",
    "Looking forward to our collaboration.",
]


class Command(BaseCommand):
    """
    Django management command to populate test chat rooms
    and messages for development/testing purposes.
    """

    help = "Populate test rooms and messages"

    @log_and_capture("populate_messages", ValidationError)
    def handle(self, *args, **options):
        """
        Main entry point for the management command.
        - Creates required user roles.
        - Creates test users.
        - Creates or retrieves a chat room between the investor and startup.
        - Populates the room with encrypted test messages.
        """
        for role_value in [UserRole.Role.INVESTOR, UserRole.Role.STARTUP]:
            UserRole.objects.get_or_create(role=role_value)

        users = {}
        for u in TEST_USERS:
            role = UserRole.objects.get(role=u["role"])
            user, created = User.objects.get_or_create(
                email=u["email"],
                defaults={
                    "first_name": u["email"].split("@")[0],
                    "last_name": "Test",
                    "password": "password123",
                    "role": role,
                    "is_active": True,
                },
            )
            users[u["email"]] = user
            logger.info("Created USER: %s", user.email)

        investor = users["investor@example.com"]
        startup = users["startup@example.com"]

        try:
            room, created = get_or_create_room(investor, startup)
            logger.info("Room created: %s | created=%s", room.name, created)
        except ValidationError as ve:
            logger.error("Failed to create TestRoom: %s", ve)
            return

        for i, text in enumerate(TEST_MESSAGES):
            sender = investor if i % 2 == 0 else startup
            receiver = startup if sender == investor else investor
            encrypted_text = encrypt_string(text)
            msg = Message(
                room=room,
                sender_email=sender.email,
                receiver_email=receiver.email,
                text=encrypted_text
            )
            msg.save()

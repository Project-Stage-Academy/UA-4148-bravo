import logging
import os
from django.core.management.base import BaseCommand
from users.documents import UserDocument, UserRoleDocument, UserRoleEnum
from chat.documents import Room, Message
from random import shuffle
from mongoengine import ValidationError

TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "testpassword123")

TEST_USERS = [
    {"email": "user1@example.com", "first_name": "User", "last_name": "One"},
    {"email": "user2@example.com", "first_name": "User", "last_name": "Two"},
    {"email": "user3@example.com", "first_name": "User", "last_name": "Three"},
]

MESSAGES = [
    "Hello everyone!",
    "How are you?",
    "All good, thanks!",
    "What's new?",
    "Who’s here?"
]

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Populate MongoDB with test users, rooms and messages"

    def handle(self, *args, **kwargs):
        role_user = UserRoleDocument.objects(role=UserRoleEnum.USER).first()
        if not role_user:
            role_user = UserRoleDocument(role=UserRoleEnum.USER).save()

        users = []
        for u in TEST_USERS:
            try:
                user = UserDocument.objects(email=u["email"]).first()
                if not user:
                    user = UserDocument(
                        email=u["email"],
                        first_name=u["first_name"],
                        last_name=u["last_name"],
                        password=TEST_USER_PASSWORD,
                        role=role_user,
                        is_active=True,
                    ).save()
                users.append(user)
            except Exception as e:
                logger.error("Failed to create user %s: %s", u.get("email"), e)

        room_name = kwargs.get('room_name', 'TestRoom')
        room = Room.objects(name=room_name).first()
        if not room:
            try:
                room = Room(name="TestRoom", participants=users).save()
                logger.info("Created test room 'TestRoom' with %d participants", len(users))
            except ValidationError as ve:
                logger.error("Failed to create test room 'TestRoom': %s", ve)
                raise ve

        num_messages = 10
        shuffled_users = users.copy()
        shuffled_texts = MESSAGES.copy()
        shuffle(shuffled_users)
        shuffle(shuffled_texts)

        for sender, text in zip(shuffled_users * ((num_messages // len(shuffled_users)) + 1),
                                shuffled_texts * ((num_messages // len(shuffled_texts)) + 1)):
            try:
                Message(room=room, sender=sender, text=text).save()
            except ValidationError as ve:
                logger.warning("Failed to save test message from %s: %s", sender.email, ve)

        self.stdout.write(self.style.SUCCESS("MongoDB populated with test data!"))

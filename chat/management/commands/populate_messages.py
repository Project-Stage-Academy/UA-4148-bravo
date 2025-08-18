from django.core.management.base import BaseCommand
from users.documents import UserDocument, UserRoleDocument, UserRoleEnum
from chat.documents import Room, Message
from random import choice

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


class Command(BaseCommand):
    help = "Populate MongoDB with test users, rooms and messages"

    def handle(self, *args, **kwargs):
        role_user = UserRoleDocument.objects(role=UserRoleEnum.USER).first()
        if not role_user:
            role_user = UserRoleDocument(role=UserRoleEnum.USER).save()

        users = []
        for u in TEST_USERS:
            user = UserDocument.objects(email=u["email"]).first()
            if not user:
                user = UserDocument(
                    email=u["email"],
                    first_name=u["first_name"],
                    last_name=u["last_name"],
                    password="pass123",
                    role=role_user,
                    is_active=True,
                ).save()
            users.append(user)

        room = Room.objects(name="TestRoom").first()
        if not room:
            room = Room(name="TestRoom", participants=users).save()

        for _ in range(10):
            sender = choice(users)
            text = choice(MESSAGES)
            Message(room=room, sender=sender, text=text).save()

        self.stdout.write(self.style.SUCCESS("MongoDB populated with test data!"))

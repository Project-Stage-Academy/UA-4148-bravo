import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import UserRole
import os
import secrets

logger = logging.getLogger(__name__)
User = get_user_model()

DEFAULT_PASSWORDS = {
    "admin": os.getenv("ADMIN_PASSWORD", secrets.token_urlsafe(12)),
    "moderator": os.getenv("MODERATOR_PASSWORD", secrets.token_urlsafe(12)),
    "user1": os.getenv("USER1_PASSWORD", secrets.token_urlsafe(12)),
    "user2": os.getenv("USER2_PASSWORD", secrets.token_urlsafe(12)),
}

class Command(BaseCommand):
    help = "Create default users with predefined roles (idempotent)."

    def handle(self, *args, **options):
        roles = {role.role: role for role in UserRole.objects.all()}
        required_roles = ["admin", "moderator", "user"]

        for r in required_roles:
            if r not in roles:
                role_obj, _ = UserRole.objects.get_or_create(role=r)
                roles[r] = role_obj
                self.stdout.write(self.style.SUCCESS(f"Role '{r}' created."))
            else:
                self.stdout.write(self.style.WARNING(f"Role '{r}' already exists."))

        users_data = [
            {
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "password": DEFAULT_PASSWORDS["admin"],
                "role": roles["admin"],
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "mod@example.com",
                "first_name": "Moderator",
                "last_name": "User",
                "password": DEFAULT_PASSWORDS["moderator"],
                "role": roles["moderator"],
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "user1@example.com",
                "first_name": "User1",
                "last_name": "Test",
                "password": DEFAULT_PASSWORDS["user1"],
                "role": roles["user"],
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "user2@example.com",
                "first_name": "User2",
                "last_name": "Test",
                "password": DEFAULT_PASSWORDS["user2"],
                "role": roles["user"],
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
            },
        ]

        for udata in users_data:
            user = User.objects.filter(email=udata["email"]).first()
            if user:
                self.stdout.write(self.style.WARNING(f"User {udata['email']} already exists."))
                continue

            user = User.objects.create_user(
                email=udata["email"],
                password=udata["password"],
                first_name=udata["first_name"],
                last_name=udata["last_name"],
                role=udata["role"],
                is_active=udata["is_active"],
            )
            user.is_staff = udata.get("is_staff", False)
            user.is_superuser = udata.get("is_superuser", False)
            user.save()

            self.stdout.write(self.style.SUCCESS(f"User {udata['email']} created successfully."))
            logger.info(f"User {user.id} created")
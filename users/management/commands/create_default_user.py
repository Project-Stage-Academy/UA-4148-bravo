import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from users.models import UserRole

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Create a default user with full fields (idempotent)."

    def handle(self, *args, **options):
        email = getattr(settings, "DEFAULT_USER_EMAIL", "first_user@example.com")
        password = getattr(settings, "DEFAULT_USER_PASSWORD", "firstuser12345")
        first_name = getattr(settings, "DEFAULT_USER_FIRST_NAME", "First")
        last_name = getattr(settings, "DEFAULT_USER_LAST_NAME", "User")

        user = User.objects.filter(email=email).first()
        if user:
            self.stdout.write(self.style.WARNING(f"User {email} already exists."))
            return

        role_user, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role_user,
            is_active=True
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()

        self.stdout.write(self.style.SUCCESS(f"Default user {email} created successfully."))
        logger.info(f"Default user {email} created")

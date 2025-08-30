import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Create a default user (idempotent — won’t duplicate if user exists)."

    def handle(self, *args, **options):
        email = getattr(settings, "DEFAULT_USER_EMAIL", "admin@example.com")
        password = getattr(settings, "DEFAULT_USER_PASSWORD", "admin12345")

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"User {email} already exists."))
            return

        user = User.objects.create_user(
            email=email,
            password=password,
            is_active=True,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save()

        self.stdout.write(self.style.SUCCESS(f"Default user {email} created successfully."))
        logger.info(f"Default user {email} created")

import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from communications.models import NotificationType, UserNotificationPreference, UserNotificationTypePreference

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Create default notification settings (idempotent)."

    def handle(self, *args, **options):
        types = {
            "new_project": NotificationType.objects.get_or_create(
                code="new_project",
                defaults={"name": "New Project", "description": "Notify investors about new startup projects."}
            )[0],
            "investor_saved_startup": NotificationType.objects.get_or_create(
                code="investor_saved_startup",
                defaults={"name": "Investor Saved Startup", "description": "Notify startups when investors save them."}
            )[0],
            "weekly_digest": NotificationType.objects.get_or_create(
                code="weekly_digest",
                defaults={"name": "Weekly Digest", "description": "Weekly summary of activity."}
            )[0],
        }

        users_map = {
            "user1@example.com": ["investor_saved_startup", "weekly_digest"],
            "user2@example.com": ["new_project", "weekly_digest"],
        }

        for email, allowed_types in users_map.items():
            user = User.objects.filter(email=email).first()
            if not user:
                self.stdout.write(self.style.WARNING(f"User {email} not found, skipping."))
                continue

            pref, _ = UserNotificationPreference.objects.get_or_create(
                user=user,
                defaults={"enable_in_app": True, "enable_email": True, "enable_push": False}
            )

            for code in allowed_types:
                nt = types.get(code)
                if nt:
                    _, created = UserNotificationTypePreference.objects.get_or_create(
                        user_preference=pref,
                        notification_type=nt,
                        defaults={"frequency": "immediate"}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Added {code} preference for {email}"))

        logger.info("Default notification settings created or already existed.")
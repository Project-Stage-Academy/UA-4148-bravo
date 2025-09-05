import logging
import os
from celery import shared_task
from django.conf import settings
from users.management.commands.cleanup_email_tokens import Command as CleanupCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from users.models import User

logger = logging.getLogger(__name__)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "forum@example.com")


@shared_task
def cleanup_email_tokens():
    """
    Celery task to clean up expired email verification tokens.
    This task is scheduled to run weekly via Celery Beat.
    """
    command = CleanupCommand()
    command.handle(days=7)


@shared_task
def send_welcome_oauth_email_task(subject, message, recipient_list):
    if subject and message and recipient_list:
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                fail_silently=False,
            )
            logger.info(f"Email was successfully sent to {recipient_list}")
            return f"Email sent to {recipient_list}"
        except Exception:
            logger.exception("Email was not sent")
            return "Failed to send email"
    else:
        logger.error("Subject, message, and recipient_list must not be empty")
        return "Invalid email parameters"


@shared_task
def check_unbound_inactive_users():
    """
    Scan for:
    - Active users not linked to Startup/Investor
    - Active users with no actions in the last 7 days
    """

    cache_key = "last_unbound_check"
    if cache.get(cache_key):
        return "Already checked recently"
    cache.set(cache_key, True, timeout=60 * 60 * 12)

    unbound_users = User.objects.filter(
        is_active=True,
        startup__isnull=True,
        investor__isnull=True,
        is_deleted=False
    )
    for user in unbound_users:
        send_mail(
            "Complete Your Company Setup",
            "Hi, please bind your account to a Startup or Investor profile.",
            DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )

    seven_days_ago = timezone.now() - timedelta(days=7)
    inactive_recent_users = User.objects.filter(
        is_active=True,
        last_action_at__lt=seven_days_ago
    )
    for user in inactive_recent_users:
        send_mail(
            "We Miss You!",
            "Hi, we noticed you haven't been active recently. Come back and check updates!",
            DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )

    return f"Processed {unbound_users.count()} unbound and {inactive_recent_users.count()} inactive users."

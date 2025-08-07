from celery import shared_task
from django.utils import timezone
from django.conf import settings
from users.management.commands.cleanup_email_tokens import Command as CleanupCommand

@shared_task
def cleanup_email_tokens():
    """
    Celery task to clean up expired email verification tokens.
    This task is scheduled to run weekly via Celery Beat.
    """
    command = CleanupCommand()
    command.handle(days=7)

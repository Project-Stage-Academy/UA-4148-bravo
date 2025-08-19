import logging
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from users.management.commands.cleanup_email_tokens import Command as CleanupCommand
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

@shared_task
def cleanup_email_tokens():
    """
    Celery task to clean up expired email verification tokens.
    This task is scheduled to run weekly via Celery Beat.
    """
    command = CleanupCommand()
    command.handle(days=7)


@shared_task
def send_email_task(subject, message, recipient_list):
    try:
        send_mail(
            subject,
            message,
            None,  # uses DEFAULT_FROM_EMAIL
            recipient_list,
            fail_silently=False,
        )
        return f"Email sent to {recipient_list}"
    except Exception as e:
        logger.critical(
            "Email was not sent",
            extra={'error': str(e)}
        )
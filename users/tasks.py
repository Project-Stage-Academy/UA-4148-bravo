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
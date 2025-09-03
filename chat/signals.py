import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from chat.documents import Message
from communications.models import Notification
from communications.tasks import send_notification_task

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Message)
def create_and_notify(sender, instance, created, **kwargs):
    """
    Signal receiver that creates a Notification and dispatches it via Celery task.

    Logs the creation of the Notification and the dispatching of the Celery task.
    """
    if created:
        notification = Notification.objects.create(
            recipient=instance.receiver,
            message=instance
        )
        logger.info(
            "[NOTIFICATION_SIGNAL] Created Notification (id=%s) for receiver=%s",
            notification.id,
            instance.receiver.email
        )

        send_notification_task.delay(
            user_id=instance.receiver.id,
            notification_data={
                "title": "New Message",
                "message": f"New message from {instance.sender.username}",
                "notification_id": str(notification.id),
            }
        )
        logger.info(
            "[NOTIFICATION_SIGNAL] Dispatched send_notification_task for user=%s, notification_id=%s",
            instance.receiver.email,
            notification.id
        )

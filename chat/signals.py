import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from chat.documents import Message
from communications.models import Notification, NotificationType
from communications.tasks import send_notification_task

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Message)
def create_and_notify(sender, instance, created, **kwargs):
    """
    Signal receiver that creates a Notification and dispatches it via Celery task.

    Logs the creation of the Notification and the dispatching of the Celery task.
    """
    notif_type = NotificationType.objects.get(code="message")

    notification = Notification.objects.create(
        user=instance.receiver,
        notification_type=notif_type,
        title="New Message",
        message=f"New message from {instance.sender.username}",
        related_message_id=str(instance.id),
        triggered_by_user=instance.sender,
        triggered_by_type="startup" if instance.sender.is_startup else "investor",  # приклад
    )

    logger.info(
        "[NOTIFICATION_SIGNAL] Created Notification (id=%s) for receiver=%s",
        notification.notification_id,
        instance.receiver.email
    )

    send_notification_task.delay(
        user_id=instance.receiver.id,
        notification_data={
            "title": notification.title,
            "message": notification.message,
            "notification_id": str(notification.notification_id),
        }
    )
    logger.info(
        "[NOTIFICATION_SIGNAL] Dispatched send_notification_task for user=%s, notification_id=%s",
        instance.receiver.email,
        notification.notification_id
    )

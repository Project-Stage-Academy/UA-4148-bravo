from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_notification_task(user_id, notification_data):
    """
    Celery task to send a notification message to the specified user.
    Args:
        user_id (int): The ID of the user who should receive the notification.
        notification_data (dict): Data to be included in the notification.
    """
    try:
        channel_layer = get_channel_layer()
        if channel_layer is not None:
            async_to_sync(channel_layer.group_send)(
                f"notifications_{user_id}",
                {
                    "type": "send_notification",
                    "notification": notification_data,
                }
            )
            logger.info("Notification sent to user %s", user_id)
    except Exception as e:
        logger.error("Failed to send notification to user %s: %s", user_id, e)

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Startup
from .documents import StartupDocument
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Startup)
def update_startup_document(sender, instance, **kwargs):
    try:
        StartupDocument().update(instance)
    except Exception as e:
        logger.warning(f"Failed to update Elasticsearch document for Startup(id={instance.id}): {e}")

@receiver(post_delete, sender=Startup)
def delete_startup_document(sender, instance, **kwargs):
    try:
        StartupDocument().delete(instance)
    except Exception as e:
        logger.warning(f"Failed to delete Elasticsearch document for Startup(id={instance.id}): {e}")

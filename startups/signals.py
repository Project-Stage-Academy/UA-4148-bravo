from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Startup
from .documents import StartupDocument

@receiver(post_save, sender=Startup)
def update_startup_document(sender, instance, **kwargs):
    StartupDocument().update(instance)

@receiver(post_delete, sender=Startup)
def delete_startup_document(sender, instance, **kwargs):
    try:
        StartupDocument(meta={"id": instance.id}).delete()
    except Exception as e:
        print(f"Error deleting startup from Elasticsearch: {e}")

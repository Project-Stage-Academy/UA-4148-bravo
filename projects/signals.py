from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Project
from .documents import ProjectDocument


@receiver(post_save, sender=Project)
def update_project(sender, instance, **kwargs):
    try:
        ProjectDocument().update(instance)
    except Exception:
        pass


@receiver(post_delete, sender=Project)
def delete_project(sender, instance, **kwargs):
    try:
        ProjectDocument().delete(instance)
    except Exception:
        pass


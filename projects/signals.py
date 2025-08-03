from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Project
from .documents import ProjectDocument

@receiver(post_save, sender=Project)
def update_project(sender, instance, **kwargs):
    ProjectDocument().update(instance)

@receiver(post_delete, sender=Project)
def delete_project(sender, instance, **kwargs):
    ProjectDocument().delete(instance)

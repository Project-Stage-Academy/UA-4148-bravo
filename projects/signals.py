from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from projects.models import Project, ProjectHistory
from projects.documents import ProjectDocument

import logging
from investments.models import Subscription
from communications.services import create_in_app_notification
from elasticsearch.exceptions import ConnectionError, NotFoundError

TRACKED_FIELDS = ['title', 'description', 'funding_goal', 'status', 'website', 'technologies_used', 'milestones']

@receiver(pre_save, sender=Project)
def store_pre_save_instance(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._pre_save_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._pre_save_instance = None
    else:
        instance._pre_save_instance = None

@receiver(post_save, sender=Project)
def handle_project_updates(sender, instance, created, **kwargs):
    """
    Tracks project updates, creates a history record, and sends
    notifications to subscribed investors.
    """
    if created:
        return

    try:
        old_instance = instance._pre_save_instance
    except AttributeError:
        return
    
    if not old_instance:
        return

    changes = {}
    for field in TRACKED_FIELDS:
        old_value = getattr(old_instance, field)
        new_value = getattr(instance, field)
        if old_value != new_value:
            changes[field] = {
                'old': str(old_value),
                'new': str(new_value)
            }

    if changes:
        ProjectHistory.objects.create(
            project=instance,
            user=getattr(instance, '_last_editor', None),
            changed_fields=changes
        )

        investor_user_ids = Subscription.objects.filter(project=instance).values_list('investor__user_id', flat=True).distinct()
        investor_users = get_user_model().objects.filter(user_id__in=investor_user_ids)
        
        for user in investor_users:
            title = f"Project '{getattr(instance, 'title', 'N/A')}' has been updated"
            startup_name = getattr(getattr(instance, 'startup', None), 'company_name', 'An anonymous startup')
            message = f"Startup '{startup_name}' has updated their project details."
            
            create_in_app_notification(
                user=user,
                type_code='project_updated',
                title=title,
                message=message,
                related_project=instance, 
                triggered_by_user=getattr(instance, '_last_editor', None),
                triggered_by_type='startup'
            )

@receiver(post_delete, sender=Project)
def delete_project(sender, instance, **kwargs):
    try:
        ProjectDocument().delete(id=instance.id)
    except (ConnectionError, NotFoundError) as e:
        logging.error(
            f"Failed to delete project {instance.id} from Elasticsearch: {e}"
        )
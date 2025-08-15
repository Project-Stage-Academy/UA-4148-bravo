import logging
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.conf import settings
from .models import UserNotificationPreference, NotificationType, UserNotificationTypePreference

logger = logging.getLogger(__name__)

_types_seeded = False  

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_notification_preferences(sender, instance, created, **kwargs):
    """
    Create default notification preferences and type preferences when a new user is created.
    """
    if created:
        preference, _ = UserNotificationPreference.objects.get_or_create(user=instance)

        notification_types = NotificationType.objects.filter(is_active=True)
        for notification_type in notification_types:
            UserNotificationTypePreference.objects.get_or_create(
                user_preference=preference,
                notification_type=notification_type,
                defaults={
                    'frequency': notification_type.default_frequency,
                },
            )


@receiver(post_migrate)
def create_initial_notification_types(sender, **kwargs):
    """
    Create initial notification types after migrations.
    This ensures the types exist even if the data migration wasn't run.
    """
    if sender.name == 'communications':
        global _types_seeded
        if _types_seeded:
            return
        from django.db import transaction

        notification_types = getattr(settings, 'COMMUNICATIONS_NOTIFICATION_TYPES', None)
        if not notification_types:
            logger.info('Skipping notification type seeding: COMMUNICATIONS_NOTIFICATION_TYPES is not set or empty')
            _types_seeded = True
            return
        
        desired_codes = {nt['code'] for nt in notification_types}
        with transaction.atomic():
            existing_codes = set(
                NotificationType.objects.filter(code__in=desired_codes)
                .values_list('code', flat=True)
            )
            to_create = [nt for nt in notification_types if nt['code'] not in existing_codes]

            if to_create:
                objs = [
                    NotificationType(
                        code=nt['code'],
                        name=nt['name'],
                        description=nt.get('description', ''),
                        default_frequency=nt.get('default_frequency', 'immediate'),
                        is_active=nt.get('is_active', True),
                    )
                    for nt in to_create
                ]
                NotificationType.objects.bulk_create(objs, ignore_conflicts=True)

        _types_seeded = True

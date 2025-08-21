import logging
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, post_migrate
from django.apps import apps
from django.dispatch import receiver

from .models import (
    UserNotificationPreference,
    NotificationType,
    UserNotificationTypePreference,
    Notification,
    NotificationTrigger,
    NotificationPriority,
)

logger = logging.getLogger(__name__)

_types_seeded = False
_handlers: list = []


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
                    "frequency": notification_type.default_frequency,
                },
            )


@receiver(post_migrate)
def create_initial_notification_types(sender, **kwargs):
    """
    Create initial notification types after migrations.
    This ensures the types exist even if the data migration wasn't run.
    """
    if sender.name == "communications":
        global _types_seeded
        if _types_seeded:
            return

        notification_types = getattr(settings, "COMMUNICATIONS_NOTIFICATION_TYPES", None)
        if not notification_types:
            logger.info(
                "Skipping notification type seeding: COMMUNICATIONS_NOTIFICATION_TYPES is not set or empty"
            )
            _types_seeded = True
            return

        desired_codes = {nt["code"] for nt in notification_types}
        with transaction.atomic():
            existing_codes = set(
                NotificationType.objects.filter(code__in=desired_codes).values_list("code", flat=True)
            )
            to_create = [nt for nt in notification_types if nt["code"] not in existing_codes]

            if to_create:
                objs = [
                    NotificationType(
                        code=nt["code"],
                        name=nt["name"],
                        description=nt.get("description", ""),
                        default_frequency=nt.get("default_frequency", "immediate"),
                        is_active=nt.get("is_active", True),
                    )
                    for nt in to_create
                ]
                NotificationType.objects.bulk_create(objs, ignore_conflicts=True)

        _types_seeded = True


def _get_or_create_ntype(code: str, name: str | None = None) -> NotificationType:
    ntype = NotificationType.objects.filter(code=code).first()
    if ntype:
        return ntype
    ntype, _ = NotificationType.objects.get_or_create(
        code=code,
        defaults={
            "name": name or code.replace("_", " ").title(),
            "description": "",
        },
    )
    return ntype

def _connect_saved_startup_signal():
    try:
        SavedStartup = apps.get_model("investors", "SavedStartup")
    except Exception:
        logger.warning("Could not resolve investors.SavedStartup")
        return

    @receiver(
        post_save,
        sender=SavedStartup,
        dispatch_uid="comm_saved_startup_created",
        weak=False,
    )
    def notify_startup_followed(sender, instance, created, **kwargs):
        if not created:
            return

        startup = getattr(instance, "startup", None)
        investor = getattr(instance, "investor", None)
        startup_user = getattr(startup, "user", None) if startup else None
        investor_user = getattr(investor, "user", None) if investor else None
        if not startup_user or not investor_user:
            return

        inv_name = getattr(investor_user, "get_full_name", lambda: "")() or getattr(
            investor_user, "email", ""
        )
        title = "New follower"
        message = f"{inv_name} followed your startup."

        ntype = _get_or_create_ntype("startup_followed", "Startup Followed")

        base_qs = Notification.objects.filter(
            user=startup_user,
            notification_type=ntype,
            triggered_by_user=investor_user,
            related_startup_id=getattr(startup, "id", None),
        )
        if base_qs.exists():
            return

        def _create():
            if Notification.objects.filter(
                user=startup_user,
                notification_type=ntype,
                triggered_by_user=investor_user,
                related_startup_id=getattr(startup, "id", None),
            ).exists():
                return

            Notification.objects.create(
                user=startup_user,
                notification_type=ntype,
                title=title,
                message=message,
                triggered_by_user=investor_user,
                triggered_by_type=NotificationTrigger.INVESTOR,
                priority=NotificationPriority.LOW,
                related_startup_id=getattr(startup, "id", None),
                action_link=f"/startups/{getattr(startup, 'id', '')}/followers",
            )

        conn = transaction.get_connection()
        if conn.in_atomic_block:
            transaction.on_commit(_create)
        else:
            _create()

    _handlers.append(notify_startup_followed)


_connect_saved_startup_signal()

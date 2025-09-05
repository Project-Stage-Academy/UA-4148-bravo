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
)

logger = logging.getLogger(__name__)

_types_seeded = False
_handlers: list = []

def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_notification_preferences(sender, instance, created, **kwargs):
    """
    Create default notification preferences and per-type preferences when a new user is created.
    """
    logger.debug(
        "[SIGNAL] create_user_notification_preferences fired",
        extra={"sig_created": bool(created), "user_id": getattr(instance, "pk", None)},
    )
    if created:
        preference, pref_created = UserNotificationPreference.objects.get_or_create(user=instance)
        logger.info(
            "[SIGNAL] UserNotificationPreference ensured",
            extra={"user_id": getattr(instance, "pk", None), "pref_created": pref_created},
        )

        notification_types = NotificationType.objects.filter(is_active=True)
        logger.debug(
            "[SIGNAL] Active notification types fetched",
            extra={"count": notification_types.count()},
        )
        for nt in notification_types:
            _, utp_created = UserNotificationTypePreference.objects.get_or_create(
                user_preference=preference,
                notification_type=nt,
                defaults={"frequency": nt.default_frequency},
            )
            if utp_created:
                logger.debug(
                    "[SIGNAL] Type preference created",
                    extra={"user_id": instance.pk, "nt_code": nt.code},
                )


@receiver(post_migrate)
def create_initial_notification_types(sender, **kwargs):
    """
    Ensure initial NotificationType rows exist after migrations.
    """
    if sender.name != "communications":
        return

    global _types_seeded
    if _types_seeded:
        logger.debug("[SIGNAL] Notification types already seeded, skipping")
        return

    logger.info("[SIGNAL] Seeding initial NotificationType records")
    notification_types = getattr(settings, "COMMUNICATIONS_NOTIFICATION_TYPES", None)
    if not notification_types:
        logger.info(
            "[SIGNAL] Skipping types seeding: COMMUNICATIONS_NOTIFICATION_TYPES not set or empty"
        )
        _types_seeded = True
        return

    desired_codes = {nt["code"] for nt in notification_types}
    logger.debug("[SIGNAL] Desired notification type codes computed", extra={"codes": list(desired_codes)})

    with transaction.atomic():
        existing_codes = set(
            NotificationType.objects.filter(code__in=desired_codes).values_list("code", flat=True)
        )
        to_create = [nt for nt in notification_types if nt["code"] not in existing_codes]
        logger.info(
            "[SIGNAL] NotificationType diff calculated",
            extra={"existing": list(existing_codes), "to_create_count": len(to_create)},
        )

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
            logger.info(
                "[SIGNAL] NotificationType bulk_create done",
                extra={"inserted_codes": [o.code for o in objs]},
            )

    _types_seeded = True
    logger.debug("[SIGNAL] Types seeding marked as done")


def _get_or_create_ntype(code: str, name: str | None = None) -> NotificationType:
    ntype = NotificationType.objects.filter(code=code).first()
    if ntype:
        logger.debug("[SIGNAL] NotificationType found", extra={"code": code, "id": ntype.pk})
        return ntype
    ntype, created = NotificationType.objects.get_or_create(
        code=code,
        defaults={"name": name or code.replace("_", " ").title(), "description": "", "is_active": True},
    )
    logger.info(
        "[SIGNAL] NotificationType ensured",
        extra={"code": code, "created_now": created, "id": getattr(ntype, "pk", None)},
    )
    return ntype

def _connect_saved_startup_signal():
    """
    Connect signal handler for SavedStartup creation using NotificationService.
    """
    try:
        SavedStartup = apps.get_model("investors", "SavedStartup")
        logger.debug("[SIGNAL] investors.SavedStartup model resolved")
    except Exception as e:
        logger.warning("Could not resolve investors.SavedStartup", exc_info=True)
        return

    @receiver(
        post_save,
        sender=SavedStartup,
        dispatch_uid="comm_saved_startup_created",
        weak=False,
    )
    def notify_startup_saved(sender, instance, created, **kwargs):
        """Signal handler that delegates to NotificationService."""
        logger.debug(
            "[SIGNAL] notify_startup_saved fired",
            extra={"sig_created": bool(created), "savedstartup_id": getattr(instance, "pk", None)},
        )
        if not created:
            logger.debug("[SIGNAL] Instance was updated, not created. Skip.")
            return

        startup = getattr(instance, "startup", None)
        investor = getattr(instance, "investor", None)

        if not startup or not getattr(startup, "pk", None):
            logger.warning(
                "[SIGNAL] Skip: startup missing/unsaved",
                extra={"savedstartup_id": getattr(instance, "pk", None)},
            )
            return
        if not investor or not getattr(investor, "pk", None):
            logger.warning(
                "[SIGNAL] Skip: investor missing/unsaved",
                extra={"savedstartup_id": getattr(instance, "pk", None)},
            )
            return

        # Resolve Django User objects for startup owner & investor
        startup_user = (
            getattr(startup, "user", None)
            or getattr(getattr(startup, "owner", None), "user", None)
            or getattr(startup, "owner", None)
        )
        investor_user = (
            getattr(investor, "user", None)
            or getattr(getattr(investor, "owner", None), "user", None)
            or getattr(investor, "owner", None)
        )

        if not getattr(startup_user, "pk", None):
            logger.warning(
                "[SIGNAL] Skip: startup_user missing",
                extra={"startup_id": getattr(startup, "pk", None)},
            )
            return
        if not getattr(investor_user, "pk", None):
            logger.warning(
                "[SIGNAL] Skip: investor_user missing",
                extra={"investor_id": getattr(investor, "pk", None)},
            )
            return

        # Use NotificationService for consistent notification creation
        def _create_notification():
            from .services import NotificationService
            try:
                NotificationService.create_startup_saved_notification(
                    startup=startup,
                    investor_user=investor_user,
                    startup_user=startup_user
                )
                logger.info(
                    "[SIGNAL] Startup saved notification created via NotificationService",
                    extra={
                        "startup_id": startup.pk,
                        "investor_user_id": investor_user.pk,
                        "startup_user_id": startup_user.pk,
                    }
                )
            except Exception as e:
                logger.error(
                    "[SIGNAL] Failed to create startup saved notification via NotificationService",
                    extra={"error": str(e)},
                    exc_info=True
                )

        # Handle transaction context
        conn = transaction.get_connection()
        if conn.in_atomic_block:
            logger.debug("[SIGNAL] In atomic block; scheduling on_commit")
            transaction.on_commit(_create_notification)
        else:
            logger.debug("[SIGNAL] Not in atomic block; creating immediately")
            _create_notification()

    _handlers.append(notify_startup_saved)
    logger.info("[SIGNAL] _connect_saved_startup_signal handler registered",
                extra={"handlers_count": len(_handlers)})


def _connect_followed_project_signal():
    """
    Connect signal handler for FollowedProject creation using NotificationService.
    """
    try:
        FollowedProject = apps.get_model("investors", "FollowedProject")
        logger.debug("[SIGNAL] investors.FollowedProject model resolved")
    except Exception as e:
        logger.warning("Could not resolve investors.FollowedProject", exc_info=True)
        return

    @receiver(
        post_save,
        sender=FollowedProject,
        dispatch_uid="comm_project_followed",
        weak=False,
    )
    def notify_project_followed(sender, instance, created, **kwargs):
        """Signal handler that delegates to NotificationService."""
        logger.debug(
            "[SIGNAL] notify_project_followed fired",
            extra={"sig_created": bool(created), "followedproject_id": getattr(instance, "pk", None)},
        )
        if not created:
            logger.debug("[SIGNAL] Instance was updated, not created. Skip.")
            return

        project = getattr(instance, "project", None)
        investor = getattr(instance, "investor", None)

        if not project or not getattr(project, "pk", None):
            logger.warning(
                "[SIGNAL] Skip: project missing/unsaved",
                extra={"followedproject_id": getattr(instance, "pk", None)},
            )
            return
        if not investor or not getattr(investor, "pk", None):
            logger.warning(
                "[SIGNAL] Skip: investor missing/unsaved",
                extra={"followedproject_id": getattr(instance, "pk", None)},
            )
            return

        # Resolve Django User objects for project owner (startup user) & investor
        project_startup = getattr(project, "startup", None)
        startup_user = None
        if project_startup:
            startup_user = (
                getattr(project_startup, "user", None)
                or getattr(getattr(project_startup, "owner", None), "user", None)
                or getattr(project_startup, "owner", None)
            )
        
        investor_user = (
            getattr(investor, "user", None)
            or getattr(getattr(investor, "owner", None), "user", None)
            or getattr(investor, "owner", None)
        )

        if not getattr(startup_user, "pk", None):
            logger.warning(
                "[SIGNAL] Skip: startup_user missing",
                extra={"project_id": getattr(project, "pk", None)},
            )
            return
        if not getattr(investor_user, "pk", None):
            logger.warning(
                "[SIGNAL] Skip: investor_user missing",
                extra={"investor_id": getattr(investor, "pk", None)},
            )
            return

        # Use NotificationService for consistent notification creation
        def _create_notification():
            from .services import NotificationService
            try:
                NotificationService.create_project_followed_notification(
                    project=project,
                    investor_user=investor_user,
                    startup_user=startup_user
                )
                logger.info(
                    "[SIGNAL] Project followed notification created via NotificationService",
                    extra={
                        "project_id": project.pk,
                        "investor_user_id": investor_user.pk,
                        "startup_user_id": startup_user.pk,
                    }
                )
            except Exception as e:
                logger.error(
                    "[SIGNAL] Failed to create project followed notification via NotificationService",
                    extra={"error": str(e)},
                    exc_info=True
                )

        # Handle transaction context
        conn = transaction.get_connection()
        if conn.in_atomic_block:
            logger.debug("[SIGNAL] In atomic block; scheduling on_commit")
            transaction.on_commit(_create_notification)
        else:
            logger.debug("[SIGNAL] Not in atomic block; creating immediately")
            _create_notification()

    _handlers.append(notify_project_followed)
    logger.info("[SIGNAL] _connect_followed_project_signal handler registered",
                extra={"handlers_count": len(_handlers)})


# Initialize handlers at import
logger.info("[SIGNAL] Initializing communications signals")
_connect_saved_startup_signal()

# Always enable FollowedProject signal now that it uses NotificationService
# This eliminates the need for ENABLE_FOLLOWED_PROJECT_SIGNAL setting
_connect_followed_project_signal()
logger.info("[SIGNAL] All notification signals enabled and using NotificationService")

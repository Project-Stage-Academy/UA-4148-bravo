import logging
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, post_migrate
from django.apps import apps
from django.dispatch import receiver
from datetime import timedelta
from django.utils import timezone

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
    def notify_startup_followed(sender, instance, created, **kwargs):
        logger.debug(
            "[SIGNAL] notify_startup_followed fired",
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

        if startup_user.pk == investor_user.pk:
            logger.info(
                "[SIGNAL] Skip: user followed own startup",
                extra={"user_id": startup_user.pk},
            )
            return

        sid = _to_int(getattr(startup, "id", None))
        if sid is None:
            logger.warning("[SIGNAL] Skip: startup id is not int-like", extra={"raw_id": getattr(startup, "id", None)})
            return
        inv_name = getattr(investor_user, "get_full_name", lambda: "")() or getattr(investor_user, "email", "")
        title = "New follower"
        message = f"{inv_name} followed your startup."

        # Ensure notification type
        ntype = NotificationType.objects.filter(code="startup_followed", is_active=True).first()
        if not ntype:
            logger.debug("[SIGNAL] NotificationType 'startup_followed' not found, creating")
            ntype = _get_or_create_ntype("startup_followed", "Startup Followed")
            
        now = timezone.now()
        second_start = now.replace(microsecond=0)
        second_end = second_start + timedelta(seconds=1)

        # Deduplication
        base_qs = Notification.objects.filter(
            user=startup_user,
            notification_type=ntype,
            triggered_by_user=investor_user,
            related_startup_id=sid,
            created_at__gte=second_start,
            created_at__lt=second_end,
        )
        if base_qs.exists():
            logger.info(
                "[SIGNAL] Duplicate",
                extra={
                    "startup_user_id": startup_user.pk,
                    "investor_user_id": investor_user.pk,
                    "startup_id": sid,
                    "second_start": second_start.isoformat(),
                },
            )
            return

        def _create():
            _now = timezone.now()
            _second_start = _now.replace(microsecond=0)
            _second_end = _second_start + timedelta(seconds=1)
            
            # double-check inside transaction/on_commit
            if Notification.objects.filter(
                user=startup_user,
                notification_type=ntype,
                triggered_by_user=investor_user,
                related_startup_id=sid,
                created_at__gte=_second_start,
                created_at__lt=_second_end,
            ).exists():
                logger.info(
                    "[SIGNAL] Duplicate within same second (re-check)",
                    extra={"startup_id": sid, "second_start": _second_start.isoformat()},
                )
                return

            notif = Notification.objects.create(
                user=startup_user,
                notification_type=ntype,
                title=title,
                message=message,
                triggered_by_user=investor_user,
                triggered_by_type=NotificationTrigger.INVESTOR,
                priority=NotificationPriority.LOW,
                related_startup_id=sid,
            )
            logger.info(
                "[SIGNAL] Notification created",
                extra={
                    "notification_id": str(getattr(notif, "notification_id", "")),
                    "user_id": startup_user.pk,
                    "startup_id": sid,
                    "investor_user_id": investor_user.pk,
                },
            )

        def safe_create():
            try:
                _create()
            except Exception:
                logger.error("[SIGNAL] Failed to create notification", exc_info=True)

        conn = transaction.get_connection()
        if conn.in_atomic_block:
            logger.debug("[SIGNAL] In atomic block; scheduling on_commit")
            transaction.on_commit(safe_create)
        else:
            logger.debug("[SIGNAL] Not in atomic block; creating immediately")
            safe_create()

    _handlers.append(notify_startup_followed)
    logger.info("[SIGNAL] _connect_saved_startup_signal handler registered",
                extra={"handlers_count": len(_handlers)})


def _connect_project_follow_signal():
    """Connect signal handler for ProjectFollow model to trigger notifications."""
    try:
        ProjectFollow = apps.get_model("investors", "ProjectFollow")
        logger.debug("[SIGNAL] investors.ProjectFollow model resolved")
    except Exception as e:
        logger.warning("Could not resolve investors.ProjectFollow", exc_info=True)
        return

    @receiver(
        post_save,
        sender=ProjectFollow,
        dispatch_uid="comm_project_followed_created",
        weak=False,
    )
    def notify_project_followed(sender, instance, created, **kwargs):
        """
        Send notification to startup when an investor follows their project.
        
        This signal is triggered when a new ProjectFollow instance is created.
        It sends a notification to the startup team informing them that an
        investor has followed their project.
        """
        logger.debug(
            "[SIGNAL] notify_project_followed fired",
            extra={"sig_created": bool(created), "project_follow_id": getattr(instance, "pk", None)},
        )
        
        if not created:
            logger.debug("[SIGNAL] Instance was updated, not created. Skip.")
            return

        project = getattr(instance, "project", None)
        investor = getattr(instance, "investor", None)

        if not project or not getattr(project, "pk", None):
            logger.warning(
                "[SIGNAL] Skip: project missing/unsaved",
                extra={"project_follow_id": getattr(instance, "pk", None)},
            )
            return
        if not investor or not getattr(investor, "pk", None):
            logger.warning(
                "[SIGNAL] Skip: investor missing/unsaved",
                extra={"project_follow_id": getattr(instance, "pk", None)},
            )
            return

        startup = getattr(project, "startup", None)
        if not startup:
            logger.warning(
                "[SIGNAL] Skip: startup missing from project",
                extra={"project_id": getattr(project, "pk", None)},
            )
            return
            
        startup_user = getattr(startup, "user", None)
        investor_user = getattr(investor, "user", None)

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

        if startup_user.pk == investor_user.pk:
            logger.info(
                "[SIGNAL] Skip: user followed own project",
                extra={"user_id": startup_user.pk},
            )
            return

        project_id = _to_int(getattr(project, "id", None))
        if project_id is None:
            logger.warning("[SIGNAL] Skip: project id is not int-like", extra={"raw_id": getattr(project, "id", None)})
            return
            
        investor_name = getattr(investor_user, "get_full_name", lambda: "")() or getattr(investor_user, "email", "")
        project_title = getattr(project, "title", "your project")
        
        title = "New Project Follower"
        message = f"{investor_name} is now following your project '{project_title}'."

        ntype = NotificationType.objects.filter(code="project_followed", is_active=True).first()
        if not ntype:
            logger.debug("[SIGNAL] NotificationType 'project_followed' not found, creating")
            ntype = _get_or_create_ntype("project_followed", "Project Followed")
            
        now = timezone.now()
        second_start = now.replace(microsecond=0)
        second_end = second_start + timedelta(seconds=1)

        base_qs = Notification.objects.filter(
            user=startup_user,
            notification_type=ntype,
            triggered_by_user=investor_user,
            related_project=project,
            created_at__gte=second_start,
            created_at__lt=second_end,
        )
        if base_qs.exists():
            logger.info(
                "[SIGNAL] Duplicate project follow notification",
                extra={
                    "startup_user_id": startup_user.pk,
                    "investor_user_id": investor_user.pk,
                    "project_id": project_id,
                    "second_start": second_start.isoformat(),
                },
            )
            return

        def _create():
            _now = timezone.now()
            _second_start = _now.replace(microsecond=0)
            _second_end = _second_start + timedelta(seconds=1)
            
            if Notification.objects.filter(
                user=startup_user,
                notification_type=ntype,
                triggered_by_user=investor_user,
                related_project=project,
                created_at__gte=_second_start,
                created_at__lt=_second_end,
            ).exists():
                logger.info(
                    "[SIGNAL] Duplicate project follow notification within same second (re-check)",
                    extra={"project_id": project_id, "second_start": _second_start.isoformat()},
                )
                return

            notif = Notification.objects.create(
                user=startup_user,
                notification_type=ntype,
                title=title,
                message=message,
                triggered_by_user=investor_user,
                triggered_by_type=NotificationTrigger.INVESTOR,
                priority=NotificationPriority.MEDIUM,
                related_project=project,
            )
            logger.info(
                "[SIGNAL] Project follow notification created",
                extra={
                    "notification_id": str(getattr(notif, "notification_id", "")),
                    "user_id": startup_user.pk,
                    "project_id": project_id,
                    "investor_user_id": investor_user.pk,
                },
            )

        def safe_create():
            try:
                _create()
            except Exception:
                logger.error("[SIGNAL] Failed to create project follow notification", exc_info=True)

        conn = transaction.get_connection()
        if conn.in_atomic_block:
            logger.debug("[SIGNAL] In atomic block; scheduling on_commit")
            transaction.on_commit(safe_create)
        else:
            logger.debug("[SIGNAL] Not in atomic block; creating immediately")
            safe_create()

    _handlers.append(notify_project_followed)
    logger.info("[SIGNAL] _connect_project_follow_signal handler registered",
                extra={"handlers_count": len(_handlers)})


# Initialize handlers at import
logger.info("[SIGNAL] Initializing communications signals")
_connect_saved_startup_signal()
_connect_project_follow_signal()

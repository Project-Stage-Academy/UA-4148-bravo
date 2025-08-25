import logging
from typing import Optional

from django.contrib.auth import get_user_model

from .models import (
    Notification,
    NotificationType,
    UserNotificationPreference,
    UserNotificationTypePreference,
    NotificationFrequency,
    NotificationChannel,
)

logger = logging.getLogger(__name__)
User = get_user_model()


def _get_user_pref(user: User) -> Optional[UserNotificationPreference]:
    try:
        return user.notification_preferences
    except UserNotificationPreference.DoesNotExist:
        return None


def get_or_create_user_pref(user: User) -> UserNotificationPreference:
    """Return user's notification preferences, creating and seeding if absent.

    Seeds per-type preferences for active NotificationType objects using
    each type's default_frequency to avoid magic strings.
    """
    pref = _get_user_pref(user)
    if pref:
        return pref
    pref = UserNotificationPreference.objects.create(user=user)
    for ntype in NotificationType.objects.filter(is_active=True):
        UserNotificationTypePreference.objects.create(
            user_preference=pref,
            notification_type=ntype,
            frequency=ntype.default_frequency,
        )
    return pref


def _get_type_pref(pref: UserNotificationPreference, ntype: NotificationType) -> Optional[UserNotificationTypePreference]:
    return pref.type_preferences.filter(notification_type=ntype).first()


def is_channel_enabled(user: User, channel: str) -> bool:
    """Return whether a channel ("in_app", "email", "push") is enabled for user.
    Falls back to True if preferences are missing (fail-open) to avoid blocking messages unintentionally.
    """
    pref = _get_user_pref(user)
    if not pref:
        return True
    normalized = str(channel).lower()
    if normalized in {NotificationChannel.IN_APP, "in-app", "inapp"}:
        return bool(pref.enable_in_app)
    if normalized == NotificationChannel.EMAIL:
        return bool(pref.enable_email)
    if normalized == NotificationChannel.PUSH:
        return bool(pref.enable_push)
    return True


def is_type_allowed(user: User, ntype: NotificationType) -> bool:
    """True if the specific notification type is not disabled for user."""
    pref = _get_user_pref(user)
    if not pref:
        return True
    type_pref = _get_type_pref(pref, ntype)
    if not type_pref:
        return True
    return type_pref.frequency != NotificationFrequency.DISABLED


def create_in_app_notification(
    *,
    user: User,
    type_code: str,
    title: str,
    message: str,
    priority: Optional[str] = None,
    related_startup_id: Optional[int] = None,
    related_project_id: Optional[int] = None,
    related_message_id: Optional[int] = None,
    triggered_by_user: Optional[User] = None,
    triggered_by_type: Optional[str] = None,
) -> Optional[Notification]:
    """
    Create an in-app Notification only if user's preferences allow it.
    Returns the Notification instance or None if suppressed by preferences.
    """
    try:
        ntype = NotificationType.objects.get(code=type_code)
    except NotificationType.DoesNotExist:
        logger.warning("Unknown notification type code: %s", type_code)
        return None

    if not is_channel_enabled(user, "in_app"):
        logger.info("Suppressing in-app notification for user=%s (channel disabled)", getattr(user, "id", None))
        return None
    if not is_type_allowed(user, ntype):
        logger.info(
            "Suppressing in-app notification for user=%s type=%s (type disabled)",
            getattr(user, "id", None), ntype.code,
        )
        return None

    return Notification.objects.create(
        user=user,
        notification_type=ntype,
        title=title,
        message=message,
        priority=priority or Notification._meta.get_field("priority").default,
        related_startup_id=related_startup_id,
        related_project_id=related_project_id,
        related_message_id=related_message_id,
        triggered_by_user=triggered_by_user,
        triggered_by_type=triggered_by_type,
    )

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
        return UserNotificationPreference.objects.get(user=user)
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


def _canonical_channel(channel: str) -> Optional[str]:
    """Normalize a channel string to a canonical value from NotificationChannel.

    Accepts variations like "in_app", "inapp", "in-app", "in app"; "email", "e-mail", "mail"; and
    "push", "push-notification", "push_notification".
    Returns one of NotificationChannel.IN_APP/EMAIL/PUSH or None if unknown.
    """
    s = str(channel or "").strip().lower()
    # unify spaces and hyphens to underscores
    s = s.replace(" ", "_").replace("-", "_")
    if s in {"in_app", "inapp"}:
        return NotificationChannel.IN_APP
    if s in {"email", "e_mail", "mail"}:
        return NotificationChannel.EMAIL
    if s in {"push", "push_notification", "pushnotification"}:
        return NotificationChannel.PUSH
    return None


def is_channel_enabled(user: User, channel: str) -> bool:
    """Return whether a channel ("in_app", "email", "push") is enabled for user.
    Falls back to True if preferences are missing (fail-open) to avoid blocking messages unintentionally.
    """
    pref = _get_user_pref(user)
    if not pref:
        return True
    normalized = _canonical_channel(channel)
    if normalized == NotificationChannel.IN_APP:
        return bool(pref.enable_in_app)
    if normalized == NotificationChannel.EMAIL:
        return bool(pref.enable_email)
    if normalized == NotificationChannel.PUSH:
        return bool(pref.enable_push)
    raise ValueError(f"Unknown notification channel: {channel}")


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
        priority=priority or Notification._meta.get_field("priority").get_default(),
        related_startup_id=related_startup_id,
        related_project_id=related_project_id,
        related_message_id=related_message_id,
        triggered_by_user=triggered_by_user,
        triggered_by_type=triggered_by_type,
    )


def create_email_notification(
    *,
    user: User,
    type_code: str,
    subject: str,
    message: str,
    template_name: str = None,
    context: dict = None,
    priority: Optional[str] = None,
    related_startup_id: Optional[int] = None,
    related_project_id: Optional[int] = None,
    related_message_id: Optional[int] = None,
    triggered_by_user: Optional[User] = None,
    triggered_by_type: Optional[str] = None,
) -> bool:
    """
    Send an email notification only if user's preferences allow it.
    Returns True if email was sent, False if suppressed by preferences.
    
    Args:
        user: The recipient user
        type_code: Notification type code
        subject: Email subject line
        message: Plain text email message content
        template_name: Optional template for HTML email
        context: Optional context dict for template rendering
        priority: Optional priority level
        related_startup_id: Optional related startup ID
        related_project_id: Optional related project ID
        related_message_id: Optional related message ID
        triggered_by_user: Optional user who triggered this notification
        triggered_by_type: Optional type of trigger (investor/startup/system)
    """
    try:
        ntype = NotificationType.objects.get(code=type_code)
    except NotificationType.DoesNotExist:
        logger.warning("Unknown notification type code: %s", type_code)
        return False

    if not is_channel_enabled(user, "email"):
        logger.info("Suppressing email notification for user=%s (email channel disabled)",
                   getattr(user, "id", None))
        return False
    if not is_type_allowed(user, ntype):
        logger.info(
            "Suppressing email notification for user=%s type=%s (type disabled)",
            getattr(user, "id", None), ntype.code,
        )
        return False

    user_pref = _get_user_pref(user)
    if user_pref:
        type_pref = _get_type_pref(user_pref, ntype)
        if type_pref and type_pref.frequency != "immediate":
            logger.info(
                "Queueing email for digest/summary for user=%s type=%s frequency=%s",
                getattr(user, "id", None), ntype.code, type_pref.frequency
            )
            return True

    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        email_context = context or {}
        email_context.update({
            'subject': subject,
            'message': message,
            'notification_type': ntype,
            'user': user,
            'priority': priority,
        })
        
        if template_name:
            html_message = render_to_string(template_name, email_context)
            plain_message = strip_tags(html_message)
        else:
            html_message = f"<html><body><h2>{subject}</h2><p>{message}</p></body></html>"
            plain_message = message
            
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=None,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(
            "Email notification sent to user=%s type=%s",
            getattr(user, "id", None), ntype.code
        )
        return True
    except Exception as e:
        logger.exception("Failed to send email notification: %s", str(e))
        return False

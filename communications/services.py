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


def should_send_email_notification(user, notification_type_code):
    """
    Check if an email notification should be sent to a user for a given notification type.
    
    Args:
        user: User instance
        notification_type_code: String code of the notification type
        
    Returns:
        bool: True if email notification should be sent, False otherwise
    """
    from .models import NotificationType, EmailNotificationPreference, UserNotificationPreference
    
    try:
        if not user:
            return False
            
        try:
            user_pref = UserNotificationPreference.objects.filter(user=user).first()
            if user_pref and not user_pref.enable_email:
                return False
        except Exception:
            pass
        
        if not hasattr(user, 'email_notification_preferences'):
            try:
                EmailNotificationPreference.objects.get_or_create(user=user)
            except Exception:
                return False
            
            if not hasattr(user, 'email_notification_preferences'):
                return False
        
        email_pref = user.email_notification_preferences
        
        try:
            notification_type = NotificationType.objects.get(code=notification_type_code)
        except NotificationType.DoesNotExist:
            return False
        
        type_pref = email_pref.types_enabled.filter(notification_type=notification_type).first()
        
        if not type_pref:
            from .models import EmailNotificationTypePreference
            type_pref = EmailNotificationTypePreference.objects.create(
                email_preference=email_pref,
                notification_type=notification_type,
                enabled=True
            )
            
        return type_pref.enabled
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Error checking email notification preferences: {e}")
        return False


def send_email_notification(
    *,
    user: User,
    type_code: str,
    subject: str,
    message: str,
    html_message: Optional[str] = None,
    related_startup_id: Optional[int] = None,
    related_project_id: Optional[int] = None,
    related_message_id: Optional[int] = None,
) -> bool:
    """
    Send an email notification to the user if their preferences allow it.
    
    Args:
        user: The recipient user
        type_code: Notification type code
        subject: Email subject
        message: Plain text message
        html_message: Optional HTML message
        related_startup_id: Optional related startup ID
        related_project_id: Optional related project ID
        related_message_id: Optional related message ID
        
    Returns:
        bool: True if the email was sent, False otherwise
    """
    if not should_send_email_notification(user, type_code):
        return False
    
    from django.core.mail import send_mail
    
    try:
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("Email notification sent to user=%s type=%s", 
                   getattr(user, "id", None), type_code)
        return True
    except Exception as e:
        logger.error("Failed to send email notification: %s", str(e))
        return False

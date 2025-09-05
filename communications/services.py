import logging
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import transaction

from projects.models import Project

from communications.models import (
    Notification,
    NotificationType,
    UserNotificationPreference,
    UserNotificationTypePreference,
    NotificationFrequency,
    NotificationChannel,
    EmailNotificationPreference,
    EmailNotificationTypePreference
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
    
    with transaction.atomic():
        pref = UserNotificationPreference.objects.create(user=user)
        active_types = NotificationType.objects.filter(is_active=True)
        to_create = [
            UserNotificationTypePreference(
                user_preference=pref,
                notification_type=ntype,
                frequency=ntype.default_frequency,
            ) for ntype in active_types
        ]
        if to_create:
            UserNotificationTypePreference.objects.bulk_create(to_create)
    return pref

def get_or_create_email_pref(user: User) -> EmailNotificationPreference:
    """Return user's email notification preferences, creating them if absent."""
    with transaction.atomic():
        email_pref, created = EmailNotificationPreference.objects.get_or_create(user=user)

        if created:
            active_types = NotificationType.objects.filter(is_active=True)
            to_create = [
                EmailNotificationTypePreference(
                    email_preference=email_pref,
                    notification_type=ntype,
                    enabled=True
                ) for ntype in active_types
            ]
            if to_create:
                EmailNotificationTypePreference.objects.bulk_create(to_create)
    return email_pref


def _get_type_pref(pref: UserNotificationPreference, ntype: NotificationType) -> Optional[UserNotificationTypePreference]:
    return pref.type_preferences.filter(notification_type=ntype).first()


def _canonical_channel(channel: str) -> Optional[str]:
    """Normalize a channel string to a canonical value from NotificationChannel.

    Accepts variations like "in_app", "inapp", "in-app", "in app"; "email", "e-mail", "mail"; and
    "push", "push-notification", "push_notification".
    Returns one of NotificationChannel.IN_APP/EMAIL/PUSH or None if unknown.
    """
    import re
    s = re.sub(r"[\s\-]+", "_", str(channel or "").strip().lower())
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
    pref = get_or_create_user_pref(user)
    if not pref:
        return True
    type_pref = _get_type_pref(pref, ntype)
    if not type_pref:
        return True
    return type_pref.frequency != NotificationFrequency.DISABLED


def create_in_app_notification(user, type_code, title, message, related_project=None, triggered_by_user=None, triggered_by_type=None, **kwargs):
    """
    Creates an in-app notification.
    """
    try:
        notification_type = NotificationType.objects.get(code=type_code)
    except NotificationType.DoesNotExist:
        logger.error(f"Attempted to create notification with non-existent type_code: {type_code}")
        return None
    
    try:
        notification_kwargs = {
            'user': user,
            'notification_type': notification_type,
            'title': title,
            'message': message,
        }
        if related_project:
            notification_kwargs['related_project'] = related_project
        if triggered_by_user:
            notification_kwargs['triggered_by_user'] = triggered_by_user
        if triggered_by_type:
            notification_kwargs['triggered_by_type'] = triggered_by_type
        
        notification_kwargs.update(kwargs)
            
        return Notification.objects.create(**notification_kwargs)
    
    except Exception as e:
        logger.error(f"Error creating in-app notification for type '{type_code}': {e}", exc_info=True)
        return None


def should_send_email_notification(user, notification_type_code):
    """
    Check if an email notification should be sent to a user for a given notification type.
    
    Args:
        user: User instance
        notification_type_code: String code of the notification type
        
    Returns:
        bool: True if email notification should be sent, False otherwise
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return False

    user_pref = get_or_create_user_pref(user)
    if not user_pref.enable_email:
        return False

    try:
        email_pref = get_or_create_email_pref(user)
        type_pref = email_pref.types_enabled.get(notification_type__code=notification_type_code)
        return type_pref.enabled
    except (EmailNotificationTypePreference.DoesNotExist, NotificationType.DoesNotExist, EmailNotificationPreference.DoesNotExist):
        logger.warning(
            f"Email notification preference for type '{notification_type_code}' not found for user {user.id}."
        )
        return False
    except Exception as e:
        logger.exception(f"Error checking email notification preferences for user {user.id}: {e}")
        return False

def send_email_notification(
    *,
    user: User,
    type_code: str,
    subject: str,
    message: str,
    html_message: Optional[str] = None,
) -> bool:
    """
    Send an email notification to the user if their preferences allow it.
    
    Args:
        user: The recipient user
        type_code: Notification type code
        subject: Email subject
        message: Plain text message
        html_message: Optional HTML message
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
        logger.error("Failed to send email notification to user %s: %s", getattr(user, "id", None), str(e), exc_info=True)
        return False

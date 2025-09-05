import logging
from typing import Optional

from django.contrib.auth import get_user_model
from projects.models import Project

from communications.models import (
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


import logging
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from typing import Optional

from .models import Notification, NotificationType, NotificationTrigger, NotificationPriority
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Centralized notification service - the single source of truth for all notification creation.
    Replaces both signal-based and direct Notification.objects.create() calls.
    """

    @staticmethod
    def _get_or_create_notification_type(code: str, name: str = None) -> NotificationType:
        """Get or create a notification type."""
        ntype, created = NotificationType.objects.get_or_create(
            code=code,
            defaults={
                'name': name or code.replace('_', ' ').title(),
                'description': f'Notification for {code}',
                'is_active': True,
                'default_frequency': 'immediate'
            }
        )
        if created:
            logger.info(f"Created notification type: {code}")
        return ntype

    @staticmethod
    def _check_duplicate_notification(
        user, notification_type, triggered_by_user=None, 
        related_project_id=None, related_startup_id=None,
        time_window_seconds=30
    ) -> bool:
        """Check if a similar notification already exists within the specified time window."""
        now = timezone.now()
        time_ago = now - timedelta(seconds=time_window_seconds)

        filters = {
            'user': user,
            'notification_type': notification_type,
            'created_at__gte': time_ago,
        }
        
        if triggered_by_user:
            filters['triggered_by_user'] = triggered_by_user
        if related_project_id:
            filters['related_project_id'] = related_project_id
        if related_startup_id:
            filters['related_startup_id'] = related_startup_id

        return Notification.objects.filter(**filters).exists()

    @classmethod
    def create_notification(
        cls,
        notification_type_code: str,
        recipient_user,
        title: str,
        message: str,
        triggered_by_user=None,
        triggered_by_type=None,
        priority=NotificationPriority.MEDIUM,
        related_project=None,
        related_startup_id=None,
        related_message_id=None,
        **kwargs
    ) -> Optional[Notification]:
        """
        Universal notification creation method.
        
        Args:
            notification_type_code: Code for the notification type
            recipient_user: User who will receive the notification
            title: Notification title
            message: Notification message
            triggered_by_user: User who triggered the notification (optional)
            triggered_by_type: Type of trigger (investor/startup/system)
            priority: Notification priority (low/medium/high)
            related_project: Related project object (optional)
            related_startup_id: Related startup ID (optional)
            related_message_id: Related message ID (optional)
            **kwargs: Additional fields for the notification
            
        Returns:
            Notification instance if created, None if skipped (duplicate/error)
        """
        try:
            logger.info(
                f"Creating notification: {notification_type_code} for user {recipient_user.id}",
                extra={
                    'notification_type': notification_type_code,
                    'recipient_id': recipient_user.id,
                    'triggered_by': triggered_by_user.id if triggered_by_user else None
                }
            )

            if not recipient_user:
                logger.warning("Cannot create notification: recipient_user is required")
                return None

            if triggered_by_user and recipient_user.pk == triggered_by_user.pk:
                logger.info(f"Skipping self-notification for user {recipient_user.pk}")
                return None

            ntype = cls._get_or_create_notification_type(
                notification_type_code, 
                kwargs.get('notification_type_name')
            )

            duplicate_exists = cls._check_duplicate_notification(
                user=recipient_user,
                notification_type=ntype,
                triggered_by_user=triggered_by_user,
                related_project_id=related_project.id if related_project else None,
                related_startup_id=related_startup_id,
                time_window_seconds=kwargs.get('deduplication_window', 30)
            )
            
            if duplicate_exists:
                logger.info(
                    f"Duplicate notification prevented: {notification_type_code} for user {recipient_user.id}",
                    extra={
                        'notification_type': notification_type_code,
                        'recipient_id': recipient_user.id,
                        'reason': 'duplicate_within_window'
                    }
                )
                return None

            notification_data = {
                'user': recipient_user,
                'notification_type': ntype,
                'title': title,
                'message': message,
                'priority': priority,
            }
            
            if triggered_by_user:
                notification_data['triggered_by_user'] = triggered_by_user
            if triggered_by_type:
                notification_data['triggered_by_type'] = triggered_by_type
            if related_project:
                notification_data['related_project'] = related_project
            if related_startup_id:
                notification_data['related_startup_id'] = str(related_startup_id)
            if related_message_id:
                notification_data['related_message_id'] = str(related_message_id)
                
            for key, value in kwargs.items():
                if key not in ['notification_type_name', 'deduplication_window'] and hasattr(Notification, key):
                    notification_data[key] = value

            notification = Notification.objects.create(**notification_data)

            logger.info(
                f"Notification created successfully: {notification.notification_id}",
                extra={
                    'notification_id': str(notification.notification_id),
                    'notification_type': notification_type_code,
                    'recipient_id': recipient_user.id,
                    'title': title
                }
            )
            
            return notification

        except Exception as e:
            logger.error(
                f"Failed to create notification: {notification_type_code}",
                extra={
                    'notification_type': notification_type_code,
                    'recipient_id': getattr(recipient_user, 'id', None),
                    'error': str(e)
                },
                exc_info=True
            )
            return None

    @classmethod
    def create_project_followed_notification(
        cls, 
        project, 
        investor_user, 
        startup_user=None
    ) -> Optional[Notification]:
        """
        Create a notification when an investor follows a project.
        
        Args:
            project: The project being followed
            investor_user: The user who followed the project
            startup_user: The startup owner (will be derived from project if not provided)
        
        Returns:
            Notification instance if created, None if skipped
        """
        try:
            if not startup_user:
                if hasattr(project, 'startup') and hasattr(project.startup, 'user'):
                    startup_user = project.startup.user
                else:
                    logger.warning(f"Cannot derive startup user for project {project.id}")
                    return None

            if not startup_user or not investor_user:
                logger.warning("Missing required users for project follow notification")
                return None

            investor_name = investor_user.first_name or investor_user.email
            project_title = getattr(project, 'title', 'your project')
            
            return cls.create_notification(
                notification_type_code='project_followed',
                recipient_user=startup_user,
                title="New project follower",
                message=f"{investor_name} started following your project '{project_title}'.",
                triggered_by_user=investor_user,
                triggered_by_type=NotificationTrigger.INVESTOR,
                priority=NotificationPriority.MEDIUM,
                related_project=project,
            )

        except Exception as e:
            logger.error(f"Failed to create project follow notification: {str(e)}", exc_info=True)
            return None

    @classmethod
    def create_startup_saved_notification(
        cls, 
        startup, 
        investor_user, 
        startup_user=None
    ) -> Optional[Notification]:
        """
        Create a notification when an investor saves a startup.
        
        Args:
            startup: The startup being saved
            investor_user: The user who saved the startup
            startup_user: The startup owner (will be derived from startup if not provided)
        
        Returns:
            Notification instance if created, None if skipped
        """
        try:
            if not startup_user:
                if hasattr(startup, 'user'):
                    startup_user = startup.user
                else:
                    logger.warning(f"Cannot derive startup user for startup {startup.id}")
                    return None

            if not startup_user or not investor_user:
                logger.warning("Missing required users for startup saved notification")
                return None

            investor_name = (
                f"{investor_user.first_name} {investor_user.last_name}".strip()
                if hasattr(investor_user, 'first_name') and investor_user.first_name
                else investor_user.get_full_name() 
                if hasattr(investor_user, 'get_full_name') and investor_user.get_full_name()
                else investor_user.email
            )
            
            return cls.create_notification(
                notification_type_code='startup_saved',
                recipient_user=startup_user,
                title="New follower",
                message=f"{investor_name} saved your startup.",
                triggered_by_user=investor_user,
                triggered_by_type=NotificationTrigger.INVESTOR,
                priority=NotificationPriority.LOW,
                related_startup_id=startup.id,
            )

        except Exception as e:
            logger.error(f"Failed to create startup saved notification: {str(e)}", exc_info=True)
            return None

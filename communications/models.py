import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from projects.models import Project

class TimeStampedModel(models.Model):
    """Abstract model for created_at and updated_at fields."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class NotificationFrequency(models.TextChoices):
    IMMEDIATE = 'immediate', _('Immediate')
    DAILY_DIGEST = 'daily_digest', _('Daily Digest')
    WEEKLY_SUMMARY = 'weekly_summary', _('Weekly Summary')
    DISABLED = 'disabled', _('Disabled')


class NotificationTrigger(models.TextChoices):
    INVESTOR = 'investor', _('Investor')
    STARTUP = 'startup', _('Startup')
    SYSTEM = 'system', _('System')


class NotificationPriority(models.TextChoices):
    LOW = 'low', _('Low')
    MEDIUM = 'medium', _('Medium')
    HIGH = 'high', _('High')


class NotificationChannel(models.TextChoices):
    """Channels for delivering notifications."""
    IN_APP = 'in_app', _('In-App')
    EMAIL = 'email', _('Email')
    PUSH = 'push', _('Push')


class NotificationType(TimeStampedModel):
    """Model to store different types of notifications."""
    code = models.SlugField(
        max_length=50,
        unique=True,
        help_text=_('Unique code for the notification type')
    )
    name = models.CharField(
        max_length=100,
        help_text=_('Human-readable name')
    )
    description = models.TextField(
        blank=True,
        help_text=_('Description of when this notification is sent')
    )
    default_frequency = models.CharField(
        max_length=20,
        choices=NotificationFrequency.choices,
        default=NotificationFrequency.IMMEDIATE,
        help_text=_('Default frequency for this notification type')
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this notification type is active')
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Notification Type')
        verbose_name_plural = _('Notification Types')

    def __str__(self):
        return self.name

    @classmethod
    def get_default_pk(cls):
        """Get or create a default notification type to use as a fallback.

        This is useful for database migrations and testing.

        Returns:
            int: The primary key of the default notification type
        """
        obj, _ = cls.objects.get_or_create(
            code='default',
            defaults={
                'name': 'Default Notification',
                'description': 'Default notification type',
            }
        )
        return obj.pk


class Notification(TimeStampedModel):
    """
    Stores notifications for users about various platform events.
    
    NOTIFICATION TRIGGER FIELD USAGE GUIDELINES:

    1. For user-initiated actions:
       - triggered_by_user: Set to the User instance
       - triggered_by_type: Set to the user's current active role ('investor' or 'startup')
       
    2. For system-generated notifications:
       - triggered_by_user: Set to None
       - triggered_by_type: Set to 'system'
       
    3. Examples:
       - Investor saves a startup: triggered_by_user=investor_user, triggered_by_type='investor'
       - Startup updates project: triggered_by_user=startup_user, triggered_by_type='startup'
       - Weekly digest email: triggered_by_user=None, triggered_by_type='system'
       - Password reset reminder: triggered_by_user=None, triggered_by_type='system'

    4. Validation Rules:
       - If triggered_by_user is set, triggered_by_type should not be 'system'
       - If triggered_by_type is 'system', triggered_by_user should be None
    """
    notification_id = models.UUIDField(unique=True, editable=False, primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.PROTECT,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()

    triggered_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_notifications'
    )
    triggered_by_type = models.CharField(
        max_length=20,
        choices=NotificationTrigger.choices,
        null=True,
        blank=True
    )

    related_startup_id = models.CharField(max_length=64, null=True, blank=True)
    related_project = models.ForeignKey(
        Project, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='notifications'
    )
    related_message_id = models.CharField(max_length=64, null=True, blank=True)

    priority = models.CharField(
        max_length=10,
        choices=NotificationPriority.choices,
        default=NotificationPriority.MEDIUM
    )
    is_read = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at'], name='idx_notif_user_read'),
            models.Index(fields=['expires_at'], name='idx_notif_expires'),
        ]

    def __str__(self):
        return f"{self.notification_type.name} - {self.user.email}"


class UserNotificationPreference(TimeStampedModel):
    """Model to store user notification preferences."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        primary_key=True
    )
    enable_in_app = models.BooleanField(
        _('Enable in-app notifications'),
        default=True
    )
    enable_email = models.BooleanField(
        _('Enable email notifications'),
        default=True
    )
    enable_push = models.BooleanField(
        _('Enable push notifications'),
        default=False
    )

    def __str__(self):
        return f"Preferences for {self.user.email}"


class UserNotificationTypePreference(TimeStampedModel):
    """Model to store user preferences for specific notification types."""
    user_preference = models.ForeignKey(
        UserNotificationPreference,
        on_delete=models.CASCADE,
        related_name='type_preferences'
    )
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.CASCADE,
        related_name='user_preferences'
    )
    frequency = models.CharField(
        max_length=20,
        choices=NotificationFrequency.choices,
        default=NotificationFrequency.IMMEDIATE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user_preference', 'notification_type'],
                name='unique_user_preference_notification_type'
            )
        ]
        verbose_name = _('User Notification Type Preference')

    def __str__(self):
        return f"{self.user_preference.user.email} - {self.notification_type.name}"


class EmailNotificationPreference(TimeStampedModel):
    """Model to store user email notification preferences."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_notification_preferences',
        primary_key=True
    )

    def __str__(self):
        return f"Email Preferences for {self.user.email}"


class EmailNotificationTypePreference(TimeStampedModel):
    """Model to store user preferences for specific notification types via email."""
    email_preference = models.ForeignKey(
        EmailNotificationPreference,
        on_delete=models.CASCADE,
        related_name='types_enabled'
    )
    notification_type = models.ForeignKey(
        NotificationType,
        on_delete=models.CASCADE,
        related_name='email_preferences'
    )
    enabled = models.BooleanField(
        _('Enabled'),
        default=True,
        help_text=_('Whether email notifications for this type are enabled')
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['email_preference', 'notification_type'],
                name='unique_email_preference_notification_type'
            )
        ]
        verbose_name = _('Email Notification Type Preference')
        verbose_name_plural = _('Email Notification Type Preferences')

    def __str__(self):
        return f"{self.email_preference.user.email} - {self.notification_type.name}"

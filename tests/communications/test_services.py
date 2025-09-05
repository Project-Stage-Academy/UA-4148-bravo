from django.test import TestCase
from communications.services import (
    get_or_create_user_pref,
    create_in_app_notification,
    should_send_email_notification,
    get_or_create_email_pref,
)
from communications.models import (
    Notification,
    NotificationType, 
    UserNotificationPreference, 
    NotificationFrequency, 
    EmailNotificationPreference,
)
from tests.factories import UserFactory
from tests.communications.factories import NotificationTypeFactory

class NotificationServicesTests(TestCase):
    """Unit tests for notification service functions."""

    def setUp(self):
        NotificationType.objects.all().delete()
        self.user = UserFactory()
        UserNotificationPreference.objects.filter(user=self.user).delete()
        
        self.nt_immediate = NotificationTypeFactory(code="immediate_type", default_frequency=NotificationFrequency.IMMEDIATE)
        self.nt_disabled = NotificationTypeFactory(code="disabled_type", default_frequency=NotificationFrequency.DISABLED)

    def test_get_or_create_user_pref_creates_defaults(self):
        """Test that get_or_create_user_pref creates preferences for a new user."""
        self.assertFalse(UserNotificationPreference.objects.filter(user=self.user).exists())
        
        pref = get_or_create_user_pref(self.user)
        
        self.assertTrue(UserNotificationPreference.objects.filter(user=self.user).exists())
        self.assertEqual(pref.user, self.user)

        self.assertEqual(pref.type_preferences.count(), 2)
        
        immediate_pref = pref.type_preferences.get(notification_type=self.nt_immediate)
        self.assertEqual(immediate_pref.frequency, NotificationFrequency.IMMEDIATE)

    def test_create_in_app_notification_success(self):
        """Test successful creation of an in-app notification."""
        notification = create_in_app_notification(
            user=self.user,
            type_code="immediate_type",
            title="Success",
            message="This should work."
        )
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, "Success")
        self.assertEqual(Notification.objects.count(), 1)

    def test_create_in_app_notification_invalid_type_code(self):
        """Test that create_in_app_notification returns None for an invalid type_code."""
        notification = create_in_app_notification(
            user=self.user,
            type_code="non_existent_type",
            title="Failure",
            message="This should not work."
        )
        self.assertIsNone(notification)
        self.assertEqual(Notification.objects.count(), 0)
        
    def test_should_send_email_notification(self):
        """Test the logic for deciding whether to send an email."""
        get_or_create_email_pref(self.user)
        self.assertTrue(should_send_email_notification(self.user, self.nt_immediate.code),
                        "Should send when all preferences are enabled by default.")

        user_pref = UserNotificationPreference.objects.get(user=self.user)
        user_pref.enable_email = False
        user_pref.save()
        self.assertFalse(should_send_email_notification(self.user, self.nt_immediate.code),
                         "Should not send when global email preference is disabled.")

        user_pref.enable_email = True
        user_pref.save()

        email_pref = EmailNotificationPreference.objects.get(user=self.user)
        type_pref = email_pref.types_enabled.get(notification_type=self.nt_immediate)
        type_pref.enabled = False
        type_pref.save()
        self.assertFalse(should_send_email_notification(self.user, self.nt_immediate.code),
                         "Should not send when specific email notification type is disabled.")

        self.assertTrue(should_send_email_notification(self.user, self.nt_disabled.code),
                        "Should send for type with 'disabled' frequency if its email preference is enabled.")

        disabled_email_pref = email_pref.types_enabled.get(notification_type=self.nt_disabled)
        disabled_email_pref.enabled = False
        disabled_email_pref.save()
        self.assertFalse(should_send_email_notification(self.user, self.nt_disabled.code),
                         "Should not send when email preference for the type is explicitly disabled.")

        self.assertFalse(should_send_email_notification(self.user, "non_existent_type"),
                         "Should not send for a non-existent notification type code.")
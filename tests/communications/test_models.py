from django.test import TestCase
from django.contrib.auth import get_user_model
from communications.models import Notification, NotificationType, NotificationPriority
from tests.factories import UserFactory
from tests.communications.factories import NotificationTypeFactory

User = get_user_model()

class NotificationModelTests(TestCase):
    """Unit tests for the Notification and NotificationType models."""

    @classmethod
    def setUpTestData(cls):
        """Set up data once for the entire test class."""
        NotificationType.objects.all().delete()
        
        cls.user = UserFactory()
        cls.notification_type = NotificationTypeFactory(code="test_event")

    def test_create_notification_type(self):
        """Ensure a NotificationType can be created successfully."""
        self.assertEqual(NotificationType.objects.count(), 1)
        self.assertEqual(self.notification_type.code, "test_event")
        self.assertEqual(str(self.notification_type), self.notification_type.name)

    def test_create_notification(self):
        """Ensure a Notification can be created with default values."""
        notification = Notification.objects.create(
            user=self.user,
            notification_type=self.notification_type,
            title="Test Notification",
            message="This is a test."
        )
        self.assertIsNotNone(notification.notification_id)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, "Test Notification")
        self.assertFalse(notification.is_read) 
        self.assertEqual(notification.priority, NotificationPriority.MEDIUM) 
        self.assertEqual(str(notification), f"{self.notification_type.name} - {self.user.email}")

    def test_notification_ordering(self):
        """Ensure notifications are ordered by creation date descending."""
        notification1 = Notification.objects.create(
            user=self.user,
            notification_type=self.notification_type,
            title="First",
            message="First message."
        )
        notification2 = Notification.objects.create(
            user=self.user,
            notification_type=self.notification_type,
            title="Second",
            message="Second message."
        )
        notifications = Notification.objects.filter(user=self.user).order_by('-created_at')
        self.assertEqual(list(notifications), [notification2, notification1])
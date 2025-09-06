from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from communications.models import NotificationType, EmailNotificationPreference, EmailNotificationTypePreference
import logging
import ddt

from startups.models import Location, Industry, Startup
from tests.factories import UserFactory
from tests.communications.factories import NotificationTypeFactory
from utils.authenticate_client import authenticate_client
from django.test.utils import override_settings

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
@ddt.ddt
class EmailNotificationPreferencesTestCase(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Silence logs produced by this test class only
        logging.disable(logging.CRITICAL)

    @classmethod
    def tearDownClass(cls):
        # Re-enable logging for the rest of the test suite
        logging.disable(logging.NOTSET)
        super().tearDownClass()

    def setUp(self):
        """Common setup using factories for user and notification types."""
        self.notification_type1, _ = NotificationType.objects.get_or_create(
            code='message_received',
            defaults={
                'name': 'Message Received',
                'description': 'Notification for received messages',
                'default_frequency': 'immediate',
                'is_active': True
            }
        )
        self.notification_type2, _ = NotificationType.objects.get_or_create(
            code='project_update',
            defaults={
                'name': 'Project Update',
                'description': 'Notification for project updates',
                'default_frequency': 'immediate',
                'is_active': True
            }
        )

        self.user = UserFactory()

        location = Location.objects.create(country="US", city="NYC", region="NY")
        industry = Industry.objects.create(name="Tech")

        Startup.objects.create(
            user=self.user,
            company_name="Test Startup",
            location=location,
            industry=industry,
            email="startup@example.com",
            founded_year=2020,
            team_size=5,
            stage="mvp"
        )

        authenticate_client(self.client, self.user)

        self.email_pref = EmailNotificationPreference.objects.create(user=self.user)
        self.type_pref1 = EmailNotificationTypePreference.objects.create(
            email_preference=self.email_pref,
            notification_type=self.notification_type1,
            enabled=True
        )
        self.type_pref2 = EmailNotificationTypePreference.objects.create(
            email_preference=self.email_pref,
            notification_type=self.notification_type2,
            enabled=False
        )

    def test_get_email_preferences(self):
        """Test retrieving email notification preferences."""
        url = reverse('communications:email-notification-preference-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.user.pk)
        
        types_enabled = response.data['types_enabled']
        self.assertEqual(len(types_enabled), 2)
        
        type_codes = {item['notification_type']['code']: item['enabled'] for item in types_enabled}
        self.assertTrue(type_codes.get('message_received'))
        self.assertFalse(type_codes.get('project_update'))

    def test_update_email_preferences(self):
        """Test updating email notification preferences."""
        url = reverse('communications:email-notification-preference-detail', kwargs={'pk': self.user.pk})
        
        data = {
            'types_enabled': [
                {
                    'notification_type_id': self.notification_type1.id,
                    'enabled': False
                },
                {
                    'notification_type_id': self.notification_type2.id,
                    'enabled': True
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.type_pref1.refresh_from_db()
        self.type_pref2.refresh_from_db()
        
        self.assertFalse(self.type_pref1.enabled)
        self.assertTrue(self.type_pref2.enabled)
        
        types_enabled = {item['notification_type']['id']: item['enabled'] for item in response.data['types_enabled']}
        self.assertFalse(types_enabled.get(self.notification_type1.id))
        self.assertTrue(types_enabled.get(self.notification_type2.id))

    def test_update_email_preferences_invalid_notification_type(self):
        """Test that an invalid notification type ID returns 400."""
        url = reverse('communications:email-notification-preference-detail', kwargs={'pk': self.user.pk})
        
        data = {
            'types_enabled': [
                {
                    'notification_type_id': 999999,
                    'enabled': True
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('notification_type_id', response.data['types_enabled'][0])

    def test_unauthorized_access(self):
        """Test that unauthorized users can't access email preferences."""
        client = APIClient()
        
        list_url = reverse('communications:email-notification-preference-list')
        response = client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        detail_url = reverse('communications:email-notification-preference-detail', kwargs={'pk': self.user.pk})
        response = client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        response = client.patch(detail_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_email_sending_service(self):
        """Test that email sending respects user preferences."""
        from communications.services import should_send_email_notification
        
        self.assertTrue(should_send_email_notification(self.user, 'message_received'))
        
        self.assertFalse(should_send_email_notification(self.user, 'project_update'))
        
        self.assertFalse(should_send_email_notification(self.user, 'nonexistent_type'))
        
        user_pref = self.user.notification_preferences
        user_pref.enable_email = False
        user_pref.save()
        
        self.assertFalse(should_send_email_notification(self.user, 'message_received'))

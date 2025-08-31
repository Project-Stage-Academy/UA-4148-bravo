from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from communications.models import NotificationType, UserNotificationPreference
import ddt
from tests.factories import UserFactory
from tests.communications.factories import NotificationTypeFactory
from rest_framework.test import APIClient
import logging
from startups.models import Startup, Industry, Location
from common.enums import Stage

User = get_user_model()


@ddt.ddt
class StartupNotificationPreferencesTestCase(APITestCase):
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
        self.notification_type1 = NotificationTypeFactory(default_frequency='immediate')
        self.notification_type2 = NotificationTypeFactory(default_frequency='daily_digest')

        # Create a regular user
        self.startup_user = UserFactory()
        self.token = Token.objects.create(user=self.startup_user)
        
        # Create a startup associated with this user
        self.industry = Industry.objects.create(name="Test Industry")
        self.location = Location.objects.create(country="US", city="Test City")
        self.startup = Startup.objects.create(
            user=self.startup_user,
            company_name="Test Startup",
            description="A startup for testing",
            industry=self.industry,
            location=self.location,
            email="test@example.com",
            founded_year=2020,
            team_size=5,
            stage=Stage.MVP
        )
        
        self.client.force_authenticate(user=self.startup_user, token=self.token)

    def test_get_startup_preferences(self):
        """Test retrieving startup notification preferences."""
        url = reverse('startups:preferences')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_id', response.data)
        self.assertEqual(response.data['user_id'], self.startup_user.pk)
        self.assertIn('enable_in_app', response.data)
        self.assertIn('enable_email', response.data)
        self.assertIn('enable_push', response.data)
        self.assertIn('type_preferences', response.data)
        self.assertIsInstance(response.data['type_preferences'], list)

    def test_update_startup_preferences(self):
        """Test updating startup notification preferences."""
        url = reverse('startups:preferences-update')
        
        data = {
            'enable_in_app': True,
            'enable_email': False,
            'enable_push': True
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['enable_in_app'])
        self.assertFalse(response.data['enable_email'])
        self.assertTrue(response.data['enable_push'])

        pref = UserNotificationPreference.objects.get(user=self.startup_user)
        self.assertTrue(pref.enable_in_app)
        self.assertFalse(pref.enable_email)
        self.assertTrue(pref.enable_push)

    def test_get_startup_email_preferences(self):
        """Test retrieving startup email notification preferences."""
        url = reverse('startups:email-preferences-get')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('enable_email', response.data)
        self.assertIn('notification_types', response.data)
        self.assertIsInstance(response.data['notification_types'], list)

        if len(response.data['notification_types']) > 0:
            type_data = response.data['notification_types'][0]
            self.assertIn('id', type_data)
            self.assertIn('code', type_data)
            self.assertIn('name', type_data)
            self.assertIn('frequency', type_data)
            self.assertIn('is_active', type_data)

    def test_update_startup_email_preferences(self):
        """Test updating startup email notification preferences."""
        url = reverse('startups:email-preferences-update')
        
        notification_types = list(NotificationType.objects.all()[:2])
        
        data = {
            'enable_email': True,
            'type_preferences': [
                {
                    'notification_type_id': notification_types[0].id,
                    'frequency': 'immediate'
                },
                {
                    'notification_type_id': notification_types[1].id,
                    'frequency': 'daily_digest'
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['enable_email'])
        
        self.assertIn('type_preferences', response.data)
        self.assertIn('updated_types', response.data)
        self.assertEqual(len(response.data['updated_types']), 2)
        self.assertIn(notification_types[0].id, response.data['updated_types'])
        self.assertIn(notification_types[1].id, response.data['updated_types'])
        
        pref = UserNotificationPreference.objects.get(user=self.startup_user)
        self.assertTrue(pref.enable_email)
        
        type_pref = pref.type_preferences.get(notification_type=notification_types[0])
        self.assertEqual(type_pref.frequency, 'immediate')
        
        type_pref = pref.type_preferences.get(notification_type=notification_types[1])
        self.assertEqual(type_pref.frequency, 'daily_digest')

    def test_update_startup_email_preferences_partial(self):
        """Test updating only startup email global toggle."""
        url = reverse('startups:email-preferences-update')
        
        data = {
            'enable_email': False
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['enable_email'])
        
        pref = UserNotificationPreference.objects.get(user=self.startup_user)
        self.assertFalse(pref.enable_email)

    def test_update_startup_email_preferences_invalid_frequency(self):
        """Test updating startup email preferences with invalid frequency."""
        url = reverse('startups:email-preferences-update')
        
        # Get a notification type to update
        notification_type = NotificationType.objects.first()
        
        data = {
            'enable_email': True,
            'type_preferences': [
                {
                    'notification_type_id': notification_type.id,
                    'frequency': 'invalid_frequency'
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('errors', response.data)

    def test_update_startup_email_preferences_invalid_type_id(self):
        """Test updating startup email preferences with invalid notification type ID."""
        url = reverse('startups:email-preferences-update')
        
        invalid_id = 99999
        
        data = {
            'enable_email': True,
            'type_preferences': [
                {
                    'notification_type_id': invalid_id,
                    'frequency': 'immediate'
                }
            ]
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        # Check if at least one error contains 'not found' message
        found_error = False
        for error in response.data.get('errors', []):
            if 'error' in error and 'not found' in error['error']:
                found_error = True
                break
        self.assertTrue(found_error, "Expected to find an error with 'not found' message")

    def test_non_startup_user_access(self):
        """Test that non-startup users can't access startup preferences."""
        # Create a non-startup user (regular user without a startup)
        non_startup_user = UserFactory()
        non_startup_token = Token.objects.create(user=non_startup_user)
        
        client = APIClient()
        client.force_authenticate(user=non_startup_user, token=non_startup_token)
        
        # Try to access startup endpoints
        get_url = reverse('startups:preferences')
        response = client.get(get_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                        'Startup preferences GET endpoint should require startup role')
        
        email_prefs_url = reverse('startups:email-preferences-get')
        response = client.get(email_prefs_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                        'Startup email preferences GET endpoint should require startup role')
        
        response = client.patch(reverse('startups:email-preferences-update'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                        'Startup email preferences PATCH endpoint should require startup role')

    def test_startup_email_preferences_unauthorized(self):
        """Test that unauthorized users can't access startup email preferences."""
        client = APIClient()
        
        get_url = reverse('startups:email-preferences-get')
        response = client.get(get_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                        'Startup email preferences GET endpoint should require authentication')
        
        patch_url = reverse('startups:email-preferences-update')
        response = client.patch(patch_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED,
                        'Startup email preferences PATCH endpoint should require authentication')

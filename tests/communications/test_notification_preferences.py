from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from communications.models import NotificationType, UserNotificationPreference
import ddt
from tests.factories import UserFactory
from tests.communications.factories import NotificationTypeFactory
from rest_framework.test import APIClient
import logging
from django.test.utils import override_settings
from utils.authenticate_client import authenticate_client
from unittest.mock import patch

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
@ddt.ddt
class NotificationPreferencesTestCase(APITestCase):
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

        self.user = UserFactory()
        authenticate_client(self.client, self.user)

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_get_notification_types(self, mocked_permission):
        """Test retrieving notification types."""
        url = reverse('communications:notification-type-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        codes = [item['code'] for item in response.data]
        self.assertIn(self.notification_type1.code, codes)
        self.assertIn(self.notification_type2.code, codes)

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_get_user_preferences(self, mocked_permission):
        """Test retrieving user notification preferences."""
        url = reverse('communications:user-notification-preference-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertTrue(len(response.data) > 0)

        user_prefs = response.data[0]
        self.assertTrue('user_id' in user_prefs)
        self.assertEqual(user_prefs['user_id'], self.user.pk)
        self.assertTrue('enable_in_app' in user_prefs)
        self.assertTrue('enable_email' in user_prefs)
        self.assertTrue('enable_push' in user_prefs)

        self.assertIn('type_preferences', user_prefs)
        self.assertIsInstance(user_prefs['type_preferences'], list)

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_update_user_preferences(self, mocked_permission):
        """Test updating user notification preferences."""
        pref = UserNotificationPreference.objects.get(user=self.user)
        url = reverse('communications:user-notification-preference-detail',
                     kwargs={'pk': self.user.pk})

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

        pref.refresh_from_db()
        self.assertTrue(pref.enable_in_app)
        self.assertFalse(pref.enable_email)
        self.assertTrue(pref.enable_push)

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    @ddt.data('immediate', 'daily_digest', 'weekly_summary')
    def test_update_notification_type_preference(self, frequency, mocked_permission):
        """
        Test updating a specific notification type preference (parameterized over valid frequencies).
        """
        pref = UserNotificationPreference.objects.get(user=self.user)
        type_pref = pref.type_preferences.first()

        url = reverse(
            'communications:user-notification-preference-update-type-preference',
            kwargs={'pk': self.user.pk}
        )

        data = {
            'notification_type_id': type_pref.notification_type.id,
            'frequency': frequency,
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['frequency'], frequency)

        type_pref.refresh_from_db()
        self.assertEqual(type_pref.frequency, frequency)

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_update_type_preference_invalid_frequency(self, mocked_permission):
        """Test that an invalid frequency value returns 400 with serializer errors."""
        pref = UserNotificationPreference.objects.get(user=self.user)
        type_pref = pref.type_preferences.first()

        url = reverse(
            'communications:user-notification-preference-update-type-preference',
            kwargs={'pk': self.user.pk}
        )
        response = self.client.patch(
            url,
            {'notification_type_id': type_pref.notification_type.id, 'frequency': 'invalid_freq'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('frequency', response.data)

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_update_type_preference_invalid_notification_type_id_non_integer(self, mocked_permission):
        """Test that a non-integer notification_type_id returns 400."""
        url = reverse(
            'communications:user-notification-preference-update-type-preference',
            kwargs={'pk': self.user.pk}
        )
        response = self.client.patch(
            url,
            {'notification_type_id': 'abc', 'frequency': 'immediate'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('error'), 'notification_type_id must be an integer')

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_update_type_preference_not_found(self, mocked_permission):
        """Test that updating a non-existent user preference returns 404."""
        another_type = NotificationTypeFactory()
        url = reverse(
            'communications:user-notification-preference-update-type-preference',
            kwargs={'pk': self.user.pk}
        )
        response = self.client.patch(
            url,
            {'notification_type_id': another_type.id, 'frequency': 'immediate'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data.get('error'), 'Notification type preference not found')

    def test_unauthorized_access(self):
        """Test that unauthorized users can't access preferences."""
        client = APIClient()

        list_url = reverse('communications:user-notification-preference-list')
        response = client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        detail_url = reverse('communications:user-notification-preference-detail',
                             kwargs={'pk': self.user.pk})
        response = client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = client.patch(detail_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        type_pref_url = reverse('communications:user-notification-preference-update-type-preference',
                                kwargs={'pk': self.user.pk})
        response = client.patch(type_pref_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_initial_preferences_created(self):
        """Test that initial preferences are created for new users."""
        new_user = User.objects.create_user(
            email='new@example.com',
            password='testpass123',
            first_name='New',
            last_name='User'
        )

        self.assertTrue(hasattr(new_user, 'notification_preferences'))
        self.assertEqual(
            new_user.notification_preferences.type_preferences.count(),
            NotificationType.objects.count()
        )

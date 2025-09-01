from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from tests.factories import StartupFactory, UserFactory
from tests.communications.factories import NotificationTypeFactory
from communications.models import UserNotificationPreference, NotificationType
from startups.models import Startup
from utils.authenticate_client import authenticate_client


@override_settings(SECURE_SSL_REDIRECT=False)
class StartupNotificationPreferencesAPITests(APITestCase):
    """Integration tests for startup notification preferences API:
    verifies retrieval, channel toggles, per-type frequency updates, and permissions.
    """
    def setUp(self):
        """Prepare two active types, create a startup user, and authenticate the client."""
        self.notification_type1 = NotificationTypeFactory()
        self.notification_type2 = NotificationTypeFactory()

        self.startup = StartupFactory()
        self.user = self.startup.user

        authenticate_client(self.client, self.user)

    def test_get_preferences_creates_defaults(self):
        """GET initializes default channel flags and seeds per-type preferences."""
        url = reverse('startup-preferences')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('enable_in_app', resp.data)
        self.assertIn('enable_email', resp.data)
        self.assertIn('enable_push', resp.data)
        self.assertIn('type_preferences', resp.data)
        pref = UserNotificationPreference.objects.get(user=self.user)
        self.assertEqual(pref.type_preferences.count(), NotificationType.objects.filter(is_active=True).count())

    def test_patch_channel_preferences(self):
        """PATCH updates enable_in_app/email/push channel toggles."""
        _ = self.client.get(reverse('startup-preferences'))

        url = reverse('startup-preferences')
        payload = {
            'enable_in_app': True,
            'enable_email': False,
            'enable_push': True,
        }
        resp = self.client.patch(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['enable_in_app'])
        self.assertFalse(resp.data['enable_email'])
        self.assertTrue(resp.data['enable_push'])

    def test_update_type_preference_valid(self):
        """PATCH per-type preference sets a valid frequency value successfully."""
        pref_resp = self.client.get(reverse('startup-preferences'))
        self.assertEqual(pref_resp.status_code, status.HTTP_200_OK)

        pref = UserNotificationPreference.objects.get(user=self.user)
        type_pref = pref.type_preferences.first()

        url = reverse('startup-preferences-update-type')
        payload = {
            'notification_type_id': type_pref.notification_type.id,
            'frequency': 'daily_digest',
        }
        resp = self.client.patch(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['frequency'], 'daily_digest')

    def test_update_type_preference_invalid_frequency(self):
        """Return 400 when frequency is invalid for a type preference update."""
        _ = self.client.get(reverse('startup-preferences'))
        pref = UserNotificationPreference.objects.get(user=self.user)
        type_pref = pref.type_preferences.first()

        url = reverse('startup-preferences-update-type')
        resp = self.client.patch(
            url,
            {'notification_type_id': type_pref.notification_type.id, 'frequency': 'invalid_freq'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('frequency', resp.data)

    def test_update_type_preference_invalid_type_id_non_integer(self):
        """Return 400 when notification_type_id is not an integer."""
        _ = self.client.get(reverse('startup-preferences'))

        url = reverse('startup-preferences-update-type')
        resp = self.client.patch(
            url,
            {'notification_type_id': 'abc', 'frequency': 'immediate'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('notification_type_id', resp.data)
        self.assertEqual(resp.data['notification_type_id'], ['A valid integer is required.'])

    def test_update_type_preference_not_found(self):
        """Return 404 when the user's seeded preferences do not include the requested type."""
        _ = self.client.get(reverse('startup-preferences'))

        another_type = NotificationTypeFactory()

        url = reverse('startup-preferences-update-type')
        resp = self.client.patch(
            url,
            {'notification_type_id': another_type.id, 'frequency': 'immediate'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(resp.data.get('error'), 'Notification type preference not found')

    def test_permission_denied_for_non_startup_user(self):
        """Non-startup authenticated users are forbidden from accessing preference endpoints."""
        other_user = UserFactory.create()
        client = APIClient()
        authenticate_client(client, other_user)

        list_url = reverse('startup-preferences')
        resp = client.get(list_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        update_url = reverse('startup-preferences-update-type')
        resp = client.patch(update_url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def tearDown(self):
        """Ensure DB cleanup to avoid cross-test contamination when using file-based SQLite."""
        UserNotificationPreference.objects.all().delete()
        NotificationType.objects.all().delete()
        Startup.objects.all().delete()

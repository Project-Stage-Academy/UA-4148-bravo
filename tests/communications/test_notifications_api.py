from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from django.utils import timezone

from communications.models import Notification, NotificationPriority
from communications.models import NotificationType
from tests.elasticsearch.factories import UserFactory
from tests.communications.factories import NotificationTypeFactory


User = get_user_model()


class NotificationsApiTestCase(APITestCase):
    def setUp(self):
        # Users
        self.user = UserFactory()
        self.other_user = UserFactory()

        # Auth as self.user (same pattern as other tests)
        self.token = Token.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user, token=self.token)

        # Notification types
        self.type_message = NotificationTypeFactory(code='message_new')
        self.type_project = NotificationTypeFactory(code='project_update')

        # Some notifications for self.user
        self.n1 = Notification.objects.create(
            user=self.user,
            notification_type=self.type_message,
            title='Msg 1',
            message='You have a new message',
            is_read=False,
            priority=NotificationPriority.MEDIUM,
            related_message_id=99,
        )
        self.n2 = Notification.objects.create(
            user=self.user,
            notification_type=self.type_project,
            title='Project Update',
            message='Project status changed',
            is_read=True,
            priority=NotificationPriority.LOW,
        )
        # Another user's notification (should not be visible)
        Notification.objects.create(
            user=self.other_user,
            notification_type=self.type_message,
            title='Other user',
            message='Hidden',
            is_read=False,
        )

    def test_list_only_current_user(self):
        url = reverse('communications:notification-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Paginated response
        self.assertIn('results', resp.data)
        ids = {item['notification_id'] for item in resp.data['results']}
        self.assertIn(str(self.n1.notification_id), ids)
        self.assertIn(str(self.n2.notification_id), ids)
        self.assertEqual(len(resp.data['results']), 2)

    def test_filters_status_and_type_and_priority(self):
        url = reverse('communications:notification-list')
        # is_read=false (unread)
        resp = self.client.get(url, {'is_read': 'false'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(all(not item['is_read'] for item in resp.data['results']))
        # type code filter
        resp = self.client.get(url, {'type': 'project_update'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(all(item['notification_type']['code'] == 'project_update' for item in resp.data['results']))
        # priority filter
        resp = self.client.get(url, {'priority': 'low'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(all(item['priority'] == 'low' for item in resp.data['results']))

    def test_filters_date_range(self):
        url = reverse('communications:notification-list')
        now = timezone.now()
        # created_after in the past -> should include our notifications
        resp = self.client.get(url, {'created_after': (now - timezone.timedelta(minutes=5)).isoformat()})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data['results']), 2)
        # created_before far future -> include
        resp = self.client.get(url, {'created_before': (now + timezone.timedelta(days=1)).isoformat()})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data['results']), 2)

    def test_retrieve_notification(self):
        url = reverse('communications:notification-detail', kwargs={'notification_id': str(self.n1.notification_id)})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['notification_id'], str(self.n1.notification_id))

    def test_mark_as_read_and_unread(self):
        # mark_as_read
        url_read = reverse('communications:notification-mark-as-read', kwargs={'notification_id': str(self.n1.notification_id)})
        resp = self.client.post(url_read)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('status', resp.data)
        self.n1.refresh_from_db()
        self.assertTrue(self.n1.is_read)
        # mark_as_unread
        url_unread = reverse('communications:notification-mark-as-unread', kwargs={'notification_id': str(self.n1.notification_id)})
        resp = self.client.post(url_unread)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.n1.refresh_from_db()
        self.assertFalse(self.n1.is_read)

    def test_mark_all_as_read_and_unread(self):
        url_all_read = reverse('communications:notification-mark-all-as-read')
        resp = self.client.post(url_all_read)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.n1.refresh_from_db(); self.n2.refresh_from_db()
        self.assertTrue(self.n1.is_read and self.n2.is_read)
        url_all_unread = reverse('communications:notification-mark-all-as-unread')
        resp = self.client.post(url_all_unread)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.n1.refresh_from_db(); self.n2.refresh_from_db()
        self.assertFalse(self.n1.is_read or self.n2.is_read)

    def test_unread_count(self):
        # ensure one unread
        self.n1.is_read = False
        self.n1.save(update_fields=['is_read'])
        self.n2.is_read = True
        self.n2.save(update_fields=['is_read'])
        url = reverse('communications:notification-unread-count')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('unread_count'), 1)

    def test_resolve_returns_redirect_payload(self):
        url = reverse('communications:notification-resolve', kwargs={'notification_id': str(self.n1.notification_id)})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('redirect', resp.data)
        redirect = resp.data['redirect']
        self.assertEqual(redirect.get('kind'), 'message')
        self.assertEqual(redirect.get('id'), 99)

    def test_delete_notification(self):
        url = reverse('communications:notification-detail', kwargs={'notification_id': str(self.n2.notification_id)})
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Notification.objects.filter(notification_id=self.n2.notification_id).exists())

    def test_create_disallowed(self):
        url = reverse('communications:notification-list')
        resp = self.client.options(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        allow_header = resp.headers.get('Allow') or resp.get('Allow') 
        self.assertIsNotNone(allow_header)
        self.assertNotIn('POST', allow_header)

    def test_unauthorized_access(self):
        client = APIClient()
        list_url = reverse('communications:notification-list')
        resp = client.get(list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        # detail
        detail_url = reverse('communications:notification-detail', kwargs={'notification_id': str(self.n1.notification_id)})
        resp = client.get(detail_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        # action
        mark_url = reverse('communications:notification-mark-as-read', kwargs={'notification_id': str(self.n1.notification_id)})
        resp = client.post(mark_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

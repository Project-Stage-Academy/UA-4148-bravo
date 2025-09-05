from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.settings import third_party_settings
from users.models import UserRole
from django.core.cache import cache
from users.tasks import send_welcome_oauth_email_task
from tests.factories import UserFactory
from uuid import uuid4
from django.db import connection

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
@patch('users.views.oauth_view.OAuthTokenObtainPairView.throttle_classes', [])
class OAuthTokenObtainPairViewTests(TestCase):
    """
    Test suite for OAuthTokenObtainPairView handling password and OAuth (Google/GitHub) authentication.
    """
    GOOGLE_PROVIDER = "google"
    GITHUB_PROVIDER = "github"

    def setUp(self):
        """Initialize test data and client"""
        cache.clear()
        self.auth_url = reverse('oauth_login')
        self.role, _ = UserRole.objects.get_or_create(role="user")

        self.oauth_user = User.objects.create_user(
            email=f"testuser_{str(uuid4())[:4]}@example.com",
            first_name='OAuth',
            last_name='User',
            role=self.role,
            is_active=True
        )
        self.oauth_user.set_unusable_password()
        self.oauth_user.save()
   
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        connection.close()

    def test_invalid_payloads(self):
        """Test failure for malformed/incomplete payloads"""
        invalid_cases = [
            {}, {"provider": self.GOOGLE_PROVIDER}, {"access_token": "abc123"},
            {"provider": "", "access_token": "abc123"},
            {"provider": self.GOOGLE_PROVIDER, "access_token": ""},
            {"provider": 123, "access_token": True},
        ]
        for payload in invalid_cases:
            with self.subTest(payload=payload):
                res = self.client.post(self.auth_url, payload, format='json')
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("error", res.data)
    def test_unsupported_provider(self):
        """Test failure for unsupported OAuth provider"""
        res = self.client.post(self.auth_url, {'provider': 'twitter', 'access_token': 'token'}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['error'], "Unsupported OAuth provider")


    @patch('users.pipelines.create_or_update_user')  
    @patch('users.views.oauth_view.load_backend')
    def test_google_oauth_sets_user_active(self, mock_load_backend, mock_create_or_update_user):
        """Test Google OAuth login sets is_active correctly based on email_verified"""
        mock_backend = MagicMock()

        active_user = User.objects.get(pk=self.oauth_user.pk)
        active_user.first_name = "Updated"
        active_user.last_name = "Name"
        active_user.save()
        mock_backend.do_auth.return_value = active_user
        mock_load_backend.return_value = mock_backend

        mock_create_or_update_user.retuen_value = {'user': active_user}

        res = self.client.post(self.auth_url, {'provider': self.GOOGLE_PROVIDER, 'access_token': 'token'}, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user = User.objects.get(email=active_user.email)
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Name')
        self.assertTrue(user.is_active)

        access_token = res.cookies.get("access_token").value
        client = APIClient()
        client.cookies['access_token'] = access_token
        protected_response = client.get('/api/v1/auth/me/')
        self.assertEqual(protected_response.status_code, 200)

    @patch('users.views.oauth_view.load_backend')
    def test_github_oauth_sets_user_inactive(self, mock_load_backend):
        """Test GitHub OAuth login sets is_active correctly based on email_verified and ensures that access token is not issued"""
        inactive_user = UserFactory(is_active=False)

        mock_backend = MagicMock()
        mock_backend.do_auth.return_value = inactive_user
        mock_load_backend.return_value = mock_backend

        res = self.client.post(self.auth_url, {'provider': self.GITHUB_PROVIDER, 'access_token': 'token'},
                               format='json')

        mock_backend.do_auth.assert_called_with('token')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Account is not active', res.data['detail'])
        user = User.objects.get(email=inactive_user.email)
        self.assertFalse(user.is_active)

    # --- Google OAuth ---
    @patch('users.views.oauth_view.load_backend')
    def test_google_oauth_new_user(self, mock_load_backend):
        """Test Google OAuth login for a new user"""
        mock_backend = MagicMock()
        new_user = UserFactory(is_active=True)
        mock_backend.do_auth.return_value = new_user
        mock_load_backend.return_value = mock_backend

        res = self.client.post(self.auth_url, {'provider': self.GOOGLE_PROVIDER, 'access_token': 'token'},
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['user']['email'], new_user.email)

    @patch('users.pipelines.create_or_update_user')  
    @patch('users.views.oauth_view.load_backend')
    def test_google_oauth_existing_user(self, mock_load_backend, mock_create_or_update_user):
        """Test Google OAuth login for existing user and profile update"""
        mock_backend = MagicMock()
        updated_user = User.objects.get(pk=self.oauth_user.pk)
        updated_user.first_name = "Updated"
        updated_user.last_name = "Name"
        updated_user.save()
        mock_backend.do_auth.return_value = updated_user
        mock_load_backend.return_value = mock_backend
        mock_create_or_update_user.return_value = {'user': updated_user}

        res = self.client.post(self.auth_url, {'provider': self.GOOGLE_PROVIDER, 'access_token': 'token'},
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user = User.objects.get(email=updated_user.email)
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Name')

    @patch('users.views.oauth_view.load_backend')
    def test_google_oauth_invalid_token(self, mock_load_backend):
        """Test authentication failure with invalid Google token"""
        mock_backend = MagicMock()
        mock_backend.do_auth.return_value = None
        mock_load_backend.return_value = mock_backend

        res = self.client.post(self.auth_url, {'provider': self.GOOGLE_PROVIDER, 'access_token': 'invalid'},
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('OAuth authentication failed', res.data['error'])

    # --- GitHub OAuth ---
    @patch('users.views.oauth_view.load_backend')
    def test_github_oauth_new_user(self, mock_load_backend):
        """Test GitHub OAuth login for a new user"""
        mock_backend = MagicMock()
        new_user = UserFactory(is_active=True)
        mock_backend.do_auth.return_value = new_user
        mock_load_backend.return_value = mock_backend

        res = self.client.post(self.auth_url, {'provider': self.GITHUB_PROVIDER, 'access_token': 'token'},
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['user']['email'], new_user.email)

    @patch('users.pipelines.create_or_update_user')
    @patch('users.views.oauth_view.load_backend')
    def test_github_oauth_existing_user(self, mock_load_backend, mock_create_or_update_user):
        """Test GitHub OAuth login for existing user and profile update"""
        mock_backend = MagicMock()
        updated_user = User.objects.get(pk=self.oauth_user.pk)
        updated_user.first_name = "Updated"
        updated_user.last_name = "Full Name"
        updated_user.save()
        mock_backend.do_auth.return_value = updated_user
        mock_load_backend.return_value = mock_backend
        mock_create_or_update_user.return_value = {'user': updated_user}

        res = self.client.post(self.auth_url, {'provider': self.GITHUB_PROVIDER, 'access_token': 'token'},
                               format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user = User.objects.get(email=updated_user.email)
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Full Name')

    @patch('users.views.oauth_view.load_backend')
    def test_oauth_missing_email(self, mock_load_backend):
        """
        Test authentication failure when OAuth provider (Google/GitHub) does not provide a verified email.
        """
        mock_backend = MagicMock()
        mock_backend.do_auth.side_effect = lambda token: User()
        mock_load_backend.return_value = mock_backend

        for provider, expected_status in [(self.GOOGLE_PROVIDER, status.HTTP_400_BAD_REQUEST),
                                          (self.GITHUB_PROVIDER, status.HTTP_400_BAD_REQUEST)]:
            with self.subTest(provider=provider):
                with patch('users.views.oauth_view.OAuthTokenObtainPairView.authenticate_with_provider') as mock_auth:
                    mock_auth.side_effect = ValueError("Email not provided by provider")
                    res = self.client.post(
                        self.auth_url,
                        {'provider': provider, 'access_token': 'fake_token'},
                        format='json'
                    )
                    self.assertEqual(res.status_code, expected_status)
                    self.assertIn('Email not provided', res.data['detail'])
    @patch('users.views.oauth_view.load_backend')
    def test_oauth_expired_token(self, mock_load_backend):
        """
        Ensure that expired or invalid OAuth tokens are rejected with 400 error.
        """
        mock_backend = MagicMock()
        mock_backend.do_auth.return_value = None  # Simulate expired/invalid token
        mock_load_backend.return_value = mock_backend

        for provider in [self.GOOGLE_PROVIDER, self.GITHUB_PROVIDER]:
            with self.subTest(provider=provider):
                res = self.client.post(
                    self.auth_url,
                    {'provider': provider, 'access_token': 'expired_token'},
                    format='json'
                )
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("OAuth authentication failed", res.data['error'])
    # --- Edge & safety ---
    @patch("users.views.oauth_view.requests.get")
    def test_no_real_http_calls(self, mock_get):
        """Ensure no real HTTP request is made"""
        fake_response = MagicMock()
        fake_response.status_code = status.HTTP_200_OK
        fake_response.json.return_value = {"email": "fake@example.com", "given_name": "Fake", "family_name": "User"}
        mock_get.return_value = fake_response

        res = self.client.post(self.auth_url, {'provider': self.GOOGLE_PROVIDER, 'access_token': 'fake'}, format='json')
        self.assertNotEqual(res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('users.views.oauth_view.load_backend')
    def test_jwt_response_sets_cookie(self, mock_load_backend):
        """Test that JWT response properly sets refresh token cookie"""
        mock_backend = MagicMock()
        active_user = self.oauth_user
        mock_backend.do_auth.return_value = active_user
        mock_load_backend.return_value = mock_backend

        res = self.client.post(self.auth_url, {'provider': self.GOOGLE_PROVIDER, 'access_token': 'token'},
                               format='json', secure=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn("access", res.data)
        self.assertNotIn("refresh", res.data)
        for key in ["access_token", "refresh_token"]:
            self.assertIn(key, res.cookies)
            cookie = res.cookies[key]
            self.assertTrue(cookie["httponly"])
            self.assertTrue(cookie["secure"])


class TestSendWelcomeEmail(TestCase):
    def setUp(self):
        """Enable Celery eager mode for synchronous task execution during tests."""
        self._orig_always_eager = third_party_settings.CELERY_TASK_ALWAYS_EAGER
        self._orig_eager_propagates = third_party_settings.CELERY_TASK_EAGER_PROPAGATES
        third_party_settings.CELERY_TASK_ALWAYS_EAGER = True
        third_party_settings.CELERY_TASK_EAGER_PROPAGATES = True
    def tearDown(self):
        """Restore original Celery settings."""
        third_party_settings.CELERY_TASK_ALWAYS_EAGER = self._orig_always_eager
        third_party_settings.CELERY_TASK_EAGER_PROPAGATES = self._orig_eager_propagates
    @patch("users.tasks.send_mail")
    def test_send_email_task_success(self, mock_send_mail):
        """
        Test that the send_welcome_oauth_email_task sends an email successfully
        when valid parameters are provided.
        """
        test_recipient_list = ["you@example.com"]
        result = send_welcome_oauth_email_task.delay("Subject", "Hello", test_recipient_list)
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.result, f"Email sent to {test_recipient_list}")
        mock_send_mail.assert_called_once_with(
            "Subject",
            "Hello",
            third_party_settings.DEFAULT_FROM_EMAIL,
            test_recipient_list,
            fail_silently=False
        )
    @patch("users.tasks.send_mail")
    def test_send_email_task_missing_params(self, mock_send_mail):
        """
        Test that the task handles missing parameters gracefully without sending an email.
        """
        result = send_welcome_oauth_email_task.delay("", "", [])
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.result, "Invalid email parameters")
        mock_send_mail.assert_not_called()
    @patch("users.tasks.send_mail", side_effect=Exception("SMTP error"))
    def test_send_email_failure(self, mock_send_mail):
        """
        Test that exceptions during sending are logged and do not fail the task.
        """
        recipients = ["valid@example.com"]
        with self.assertLogs("users.tasks", level="ERROR") as cm:
            result = send_welcome_oauth_email_task.delay("Subject", "Hello", recipients)

        self.assertEqual(result.status, "SUCCESS")
        self.assertIn("Email was not sent", "\n".join(cm.output))
        mock_send_mail.assert_called_once()

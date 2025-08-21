import requests_mock
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import UserRole
from django.test import override_settings
from django.conf import settings
from django.core.cache import cache

from users.tasks import send_welcome_oauth_email_task

User = get_user_model()

@patch('users.views.OAuthTokenObtainPairView.throttle_classes', [])
class OAuthTokenObtainPairViewTests(TestCase):
    """
    Test suite for the extended OAuthTokenObtainPairView that handles both
    password and OAuth (Google/GitHub) authentication.

    Endpoint tested:
        - POST api/v1/auth/oauth/login/  (OAuth authentication for Google and GitHub)
    """
    
    def setUp(self):
        """
        Initialize test data and client
        """
        self.client = APIClient()
        self.auth_url = reverse('oauth_login')
        self.role, _ = UserRole.objects.get_or_create(role="user")
        
        # Test users                 
        self.oauth_user = User.objects.create_user(
            email='oauth@example.com',
            first_name='OAuth',
            last_name='User',
            role=self.role
        )
        self.oauth_user.set_unusable_password()
        self.oauth_user.save()


    # ------------------------------
    # Negative / malformed payloads
    # ------------------------------
    def test_invalid_payloads(self):
        """
        Test authentication failure for various malformed or incomplete payloads.
        """
        invalid_cases = [
            {},  # empty
            {"provider": "google"},  # missing token
            {"access_token": "abc123"},  # missing provider
            {"provider": "", "access_token": "abc123"},  # blank provider
            {"provider": "google", "access_token": ""},  # blank token
            {"provider": 123, "access_token": True},  # wrong types
        ]
        for payload in invalid_cases:
            with self.subTest(payload=payload):
                res = self.client.post(self.auth_url, payload, format='json')
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("error", res.data)

    def test_unsupported_provider(self):
        """
        Test authentication failure when using an unsupported OAuth provider.
        """
        res = self.client.post(self.auth_url, {
            'provider': 'twitter',
            'access_token': 'twitter_token'
        }, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['error'], "Unsupported OAuth provider")

    # --- Google OAuth Tests ---
    def test_google_oauth_new_user(self):
        """
        Test Google OAuth login for a brand-new user and ensure user is created.
        """
        google_response = {
            "email": "newgoogle@example.com",
            "given_name": "New",
            "family_name": "GoogleUser",
            "picture": "http://example.com/pic.jpg"
        }

        with requests_mock.Mocker() as m:
            m.get('https://www.googleapis.com/oauth2/v3/userinfo', 
                 json=google_response)
            
            response = self.client.post(
                self.auth_url,
                {
                    'provider': 'google',
                    'access_token': 'valid_google_token'
                },
                format='json'
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email='newgoogle@example.com').exists())
        user = User.objects.get(email='newgoogle@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'GoogleUser')

    def test_google_oauth_existing_user(self):
        """
        Test Google OAuth login for an existing user and ensure profile is updated.
        """
        google_response = {
            "email": "oauth@example.com",
            "given_name": "Updated",
            "family_name": "Name",
        }

        with requests_mock.Mocker() as m:
            m.get('https://www.googleapis.com/oauth2/v3/userinfo', 
                 json=google_response)
            
            response = self.client.post(
                self.auth_url,
                {
                    'provider': 'google',
                    'access_token': 'valid_google_token'
                },
                format='json'
            )

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email='oauth@example.com')
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Name')

    def test_google_oauth_invalid_token(self):
        """
        Test authentication failure with invalid Google access token.
        """
        with requests_mock.Mocker() as m:
            m.get('https://www.googleapis.com/oauth2/v3/userinfo', 
                 status_code=400)
            
            response = self.client.post(
                self.auth_url,
                {
                    'provider': 'google',
                    'access_token': 'invalid_token'
                },
                format='json'
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Invalid Google token')

    def test_google_missing_email(self):
        """
        Test authentication failure with email missing.
        """
        google_response = {"given_name": "John"}
        with requests_mock.Mocker() as m:
            m.get('https://www.googleapis.com/oauth2/v3/userinfo', json=google_response)
            res = self.client.post(self.auth_url, {
                'provider': 'google',
                'access_token': 'valid_google_token'
            }, format='json')
        self.assertEqual(res.status_code, 400)
        self.assertIn('Email not provided', res.data['error'])

    # --- GitHub OAuth Tests ---
    def test_github_oauth_new_user(self):
        """
        Test successful authentication with GitHub OAuth for a new user.
        Verifies proper handling of GitHub's email endpoint.
        """
        github_user_response = {
            "login": "newgithubuser",
            "name": "GitHub New User",
            "email": None  # Intentionally missing to test email endpoint
        }

        github_emails_response = [
            {
                "email": "secondary@example.com",
                "primary": False,
                "verified": True
            },
            {
                "email": "primary@example.com",
                "primary": True,
                "verified": True
            }
        ]

        with requests_mock.Mocker() as m:
            m.get('https://api.github.com/user', json=github_user_response)
            m.get('https://api.github.com/user/emails', json=github_emails_response)
            
            response = self.client.post(
                self.auth_url,
                {
                    'provider': 'github',
                    'access_token': 'valid_github_token'
                },
                format='json'
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['email'], 'primary@example.com')

    def test_github_oauth_existing_user(self):
        """
        Test successful authentication with GitHub OAuth for an existing user.
        Verifies username and name fields are properly updated.
        """
        github_user_response = {
            "login": "updatedgithubusername",
            "name": "Updated Full Name",
            "email": "oauth@example.com"
        }

        with requests_mock.Mocker() as m:
            m.get('https://api.github.com/user', json=github_user_response)
            
            m.get(
                'https://api.github.com/user/emails',
                json=[
                    {
                        "email": "oauth@example.com",
                        "verified": True,
                        "primary": True
                    }
                ]
            )

            response = self.client.post(
                self.auth_url,
                {
                    'provider': 'github',
                    'access_token': 'valid_github_token'
                },
                format='json'
            )

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email='oauth@example.com')
        self.assertEqual(user.first_name, 'Updated')
        self.assertEqual(user.last_name, 'Full Name')

    def test_github_oauth_missing_email(self):
        """
        Test authentication failure when GitHub doesn't provide a verified email.
        """
        github_user_response = {
            "login": "noemailuser",
            "name": "No Email User"
        }

        with requests_mock.Mocker() as m:
            m.get('https://api.github.com/user', json=github_user_response)
            m.get('https://api.github.com/user/emails', json=[])
            
            response = self.client.post(
                self.auth_url,
                {
                    'provider': 'github',
                    'access_token': 'valid_github_token'
                },
                format='json'
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['error'], 'Email not provided by GitHub')

    # ------------------------------
    # Edge & safety tests
    # ------------------------------
    @patch("users.views.requests.get")
    def test_no_real_http_calls(self, mock_get):
        from unittest.mock import Mock
        """
        Ensure no real HTTP request is made by mocking requests.get.
        """
        fake_response = Mock()
        fake_response.status_code = 200
        fake_response.json.return_value = {
            "email": "fake@example.com",
            "given_name": "Fake",
            "family_name": "User"
        }
        mock_get.return_value = fake_response  # No real call

        res = self.client.post(
            self.auth_url,
            {'provider': 'google', 'access_token': 'fake'},
            format='json'
        )

        self.assertNotEqual(res.status_code, 500) 

    def test_refresh_token_flow(self):
        """
        Test refreshing JWT access token using a valid refresh token.
        """
        user = User.objects.create_user(email="refresh@example.com", password="pass1234", role=self.role)
        user.is_active = True
        user.save()
        
        refresh = RefreshToken.for_user(user)
        res = self.client.post(reverse("jwt-refresh"), {"refresh": str(refresh)}, format='json')

        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.data)

    def test_jwt_token_structure_and_validity(self):
        """
        Test that issued JWT tokens are valid and contain expected claims.
        """
        google_response = {
            "email": "jwt_test@example.com",
            "given_name": "JWT",
            "family_name": "Test"
        }

        with requests_mock.Mocker() as m:
            m.get('https://www.googleapis.com/oauth2/v3/userinfo', json=google_response)
            
            response = self.client.post(
                self.auth_url,
                {
                    'provider': 'google',
                    'access_token': 'valid_token'
                },
                format='json'
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        user = User.objects.get(email="jwt_test@example.com")
        self.assertTrue(user.is_active)

        # Verify token structure
        access_token = response.data['access']
        refresh_token = response.data['refresh']
        
        # Test token can be used for authentication
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Test protected endpoint
        protected_response = client.get('/api/v1/auth/me/')
        self.assertEqual(protected_response.status_code, 200)


    def test_token_refresh_integration(self):
        """
        Test that refresh tokens actually work to obtain new access tokens.
        """
        # First get tokens via OAuth
        google_response = {
            "email": "refresh_test@example.com",
            "given_name": "Refresh",
            "family_name": "Test"
        }

        with requests_mock.Mocker() as m:
            m.get('https://www.googleapis.com/oauth2/v3/userinfo', json=google_response)
            
            response = self.client.post(
                self.auth_url,
                {
                    'provider': 'google',
                    'access_token': 'valid_token'
                },
                format='json'
            )

        refresh_token = response.data['refresh']
        
        # Use refresh token to get new access token
        refresh_response = self.client.post(
            reverse('jwt-refresh'),
            {'refresh': refresh_token},
            format='json'
        )
        
        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn('access', refresh_response.data)
            
    def test_provider_unexpected_shape(self):
        """
        Test failure when OAuth provider response JSON is not a dictionary.
        """
        with patch("users.views.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = "not_a_dict"
            mock_get.return_value.raise_for_status.return_value = None
            res = self.client.post(self.auth_url, {
                'provider': 'google',
                'access_token': 'valid'
            }, format='json')
        self.assertIn(res.status_code, [400, 502])


class TestSendWelcomeEmail(TestCase):
    """
    Test suite for the send_welcome_oauth_email_task Celery task.
    
    Tests email functionality for OAuth user registration, including:
    - Successful email sending
    - Error handling for missing parameters
    - Exception handling for email delivery failures
    - Integration with OAuth flow
    """    
    def setUp(self):
        """
        Set up test environment for Celery task testing.

        Enables eager execution mode for Celery tasks to run synchronously
        during testing
        """
        self._orig_always_eager = settings.CELERY_TASK_ALWAYS_EAGER
        self._orig_eager_propagates = settings.CELERY_TASK_EAGER_PROPAGATES
        settings.CELERY_TASK_ALWAYS_EAGER = True
        settings.CELERY_TASK_EAGER_PROPAGATES = True

        self.auth_url = reverse('oauth_login')

    def tearDown(self):
        """
        Clean up test environment after each test.
        
        Restores original Celery settings to avoid affecting other tests.
        """
        settings.CELERY_TASK_ALWAYS_EAGER = self._orig_always_eager
        settings.CELERY_TASK_EAGER_PROPAGATES = self._orig_eager_propagates 

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()
        
    @patch("users.tasks.send_mail")
    def test_send_email_task_success(self, mock_send_mail):
        """
        Test successful execution of the welcome email task.
        """
        test_recipient_list = ["you@example.com"]
        result = send_welcome_oauth_email_task.delay("Subject", "Hello", test_recipient_list)
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.result, f"Email sent to {test_recipient_list}")

        mock_send_mail.assert_called_once_with(
            "Subject",
            "Hello",
            settings.DEFAULT_FROM_EMAIL,
            test_recipient_list,
            fail_silently=False
        )

    @patch("users.tasks.send_mail")
    def test_send_email_task_missing_params(self, mock_send_mail):
        """
        Test email task behavior with missing or empty parameters.
        """        
        # Empty subject/message/recipient_list
        result = send_welcome_oauth_email_task.delay("", "", [])

        self.assertEqual(result.status, "SUCCESS")  
        self.assertEqual(result.result, "Invalid email parameters")
        mock_send_mail.assert_not_called()    

    @patch("users.tasks.send_mail", side_effect=Exception("SMTP error"))
    def test_send_email_failure(self, mock_send_mail):
        """
        Test email task exception handling during send failure.
        """
        recipients = ["valid@example.com"]
        with self.assertLogs("users.tasks", level="ERROR") as cm:
            result = send_welcome_oauth_email_task.delay("Subject", "Hello", recipients)

        self.assertEqual(result.status, "SUCCESS")
        self.assertIn("Email was not sent", "\n".join(cm.output))
        mock_send_mail.assert_called_once()    

    @patch("users.tasks.send_mail")
    def test_complete_oauth_flow_with_email(self, mock_email_task):
        """
        Test complete OAuth flow including user creation, JWT issuance, and email sending.
        """
        google_response = {
            "email": "integration@example.com",
            "given_name": "Integration",
            "family_name": "Test"
        }

        with requests_mock.Mocker() as m:
            m.get('https://www.googleapis.com/oauth2/v3/userinfo', json=google_response)
            
            response = self.client.post(
                self.auth_url,
                {
                    'provider': 'google',
                    'access_token': 'valid_token'
                },
                format='json'
            )

        # Verify all steps completed
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Verify user was created
        user = User.objects.get(email='integration@example.com')
        self.assertEqual(user.first_name, 'Integration')
        
        # Verify email task was called
        mock_email_task.assert_called_once()    
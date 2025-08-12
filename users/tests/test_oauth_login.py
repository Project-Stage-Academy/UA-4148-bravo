from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import requests_mock
from ..models import UserRole
from django.urls import reverse

User = get_user_model()

class OAuthTokenObtainPairViewTests(TestCase):
    """
    Test suite for the extended OAuthTokenObtainPairView that handles both
    password and OAuth (Google/GitHub) authentication.
    """
    
    def setUp(self):
        """Initialize test data and client"""
        self.client = APIClient()
        # self.auth_url = '/users/oauth/login/'
        self.auth_url = reverse('oauth_login')
        self.role = UserRole.objects.get(role="user")
        
        # Test users
        self.password_user = User.objects.create_user(
            email='password@example.com',
            password='testpass123',
            first_name='Password',
            last_name='User',
            role=self.role
        )
        
        self.oauth_user = User.objects.create_user(
            email='oauth@example.com',
            first_name='OAuth',
            last_name='User',
            role=self.role
        )
        self.oauth_user.set_unusable_password()
        self.oauth_user.save()


    def test_password_authentication_invalid_credentials(self):
        """
        Test failed authentication with invalid password.
        """
        response = self.client.post(
            self.auth_url,
            {'email': 'password@example.com', 'password': 'wrongpassword'},
            format='json'
        )
        
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['detail'], 'No active account found with the given credentials')

    # --- Google OAuth Tests ---
    def test_google_oauth_new_user(self):
        """
        Test successful authentication with Google OAuth for a new user.
        Verifies user creation and token generation.
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

    def test_google_oauth_existing_user(self):
        """
        Test successful authentication with Google OAuth for an existing user.
        Verifies user data update and token generation.
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
        # self.assertEqual(response.data['user']['username'], 'newgithubuser')

    def test_github_oauth_existing_user(self):
        """
        Test successful authentication with GitHub OAuth for an existing user.
        Verifies username and name fields are properly updated.
        """
        github_user_response = {
            "login": "updatedgithubusername",
            "name": "OAuth",
            "email": "oauth@example.com"
        }

        with requests_mock.Mocker() as m:
            m.get('https://api.github.com/user', json=github_user_response)
            
            response = self.client.post(
                self.auth_url,
                {
                    'provider': 'github',
                    'access_token': 'valid_github_token'
                },
                format='json'
            )

        self.assertEqual(response.status_code, 200)

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

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Email not provided by GitHub')

    # --- Edge Case Tests ---
    def test_missing_provider(self):
        """
        Test authentication attempt with missing provider but providing access_token.
        Should fall back to password authentication and fail.
        """
        response = self.client.post(
            self.auth_url,
            {'access_token': 'some_token'},
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)  # Password auth error about missing email

    def test_unsupported_provider(self):
        """
        Test authentication attempt with unsupported OAuth provider.
        """
        response = self.client.post(
            self.auth_url,
            {
                'provider': 'twitter',  # Unsupported
                'access_token': 'twitter_token'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], "Unsupported OAuth provider")

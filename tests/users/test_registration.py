import json
from unittest.mock import patch
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User, UserRole


@override_settings(SECURE_SSL_REDIRECT=False)
class UserRegistrationTests(APITestCase):
    """Test suite for user registration functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.register_url = '/api/v1/auth/register/'
        self.valid_payload = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'TestPass123',
            'password2': 'TestPass123',
        }

        try:
            self.user_role = UserRole.objects.get(role=UserRole.Role.USER)
        except UserRole.DoesNotExist:
            self.user_role = UserRole.objects.create(
                role=UserRole.Role.USER,
                description='Regular user'
            )
    
    def test_valid_registration(self):
        """Test user registration with valid data."""
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'success')
        
        user = User.objects.get(email=self.valid_payload['email'])
        self.assertEqual(user.email, self.valid_payload['email'])
        self.assertEqual(user.first_name, self.valid_payload['first_name'])
        self.assertEqual(user.last_name, self.valid_payload['last_name'])
        self.assertTrue(user.check_password(self.valid_payload['password']))
        self.assertFalse(user.is_active)  
        self.assertIsNotNone(user.email_verification_token)
    
    def test_registration_with_existing_email(self):
        """Test registration with an email that's already registered."""
        User.objects.create_user(
            email='test@example.com',
            first_name='Existing',
            last_name='User',
            password='TestPass123',
            role=self.user_role
        )
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('email', response.data['errors'])
    
    def test_registration_with_missing_fields(self):
        """Test registration with missing required fields."""
        invalid_payload = {
            'email': 'test@example.com',
            'password': 'TestPass123',
            'password2': 'TestPass123',
        }
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data['errors'])
        self.assertIn('last_name', response.data['errors'])
    
    def test_registration_with_password_mismatch(self):
        """Test registration with non-matching passwords."""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['password2'] = 'DifferentPass123'
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertIn('password', response.data['errors'])
    
    @patch('users.views.auth_views.send_mail')
    def test_verification_email_sent(self, mock_send_mail):
        """Test that verification email is sent after registration."""  
        from django.core.cache import cache
        cache.clear()
        
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(mock_send_mail.called)
        
        args, kwargs = mock_send_mail.call_args
        self.assertEqual(kwargs['recipient_list'], [self.valid_payload['email']])
    
    @patch('users.views.auth_views.send_mail')
    def test_verification_email_content(self, mock_send_mail):
        """Test the content of the verification email."""
        response = self.client.post(
            self.register_url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(email=self.valid_payload['email'])
        
        self.assertTrue(mock_send_mail.called)
        args, kwargs = mock_send_mail.call_args
        
        self.assertEqual(kwargs['recipient_list'], [self.valid_payload['email']])
        self.assertIn('verify', kwargs['subject'].lower())
        
        html_content = kwargs['html_message']
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse

        soup = BeautifulSoup(html_content, 'html.parser')
        
        verification_link = None
        for a_tag in soup.find_all('a', href=True):
            if 'verify-email' in a_tag['href']:
                verification_link = a_tag['href']
                break
                
        self.assertIsNotNone(verification_link, "Verification link not found in email")
        
        parsed_url = urlparse(verification_link)
        path_parts = [part for part in parsed_url.path.strip('/').split('/') if part]
        
        self.assertGreaterEqual(len(path_parts), 3, f"Unexpected URL format: {verification_link}")
        self.assertEqual(path_parts[-3], 'verify-email')
        
        user_id = path_parts[-2]
        token = path_parts[-1]
        
        self.assertEqual(str(user.user_id), user_id, "User ID in verification link doesn't match")
        
        user.pending_email = user.email
        user.email_verification_token = token
        user.email_verification_sent_at = timezone.now()
        user.save()
        
        verification_url = reverse('verify-email',
                                   kwargs={'user_id': user_id, 'token': token})
        response = self.client.get(verification_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@override_settings(SECURE_SSL_REDIRECT=False)
class EmailVerificationTests(APITestCase):
    """Test email verification functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        try:
            self.user_role = UserRole.objects.get(role=UserRole.Role.USER)
        except UserRole.DoesNotExist:
            self.user_role = UserRole.objects.create(
                role=UserRole.Role.USER,
                description='Regular user'
            )
            
        self.verification_token = 'test-verification-token'
        
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='TestPass123',
            role=self.user_role,
            is_active=False
        )
        self.user.pending_email = self.user.email
        self.user.email_verification_token = self.verification_token
        self.user.email_verification_sent_at = timezone.now()
        self.user.save()
    
    def test_verification_with_valid_token(self):
        """Test verification with a valid token."""
        self.user.email_verification_sent_at = timezone.now()
        self.user.pending_email = None
        self.user.save(update_fields=['email_verification_sent_at', 'pending_email'])
        
        verification_url = reverse('verify-email',
                                   kwargs={'user_id': self.user.user_id, 'token': self.verification_token})
        response = self.client.get(verification_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['message'], 'Email verified successfully. You can now log in.')
        
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.email_verification_token)
        self.assertIsNone(self.user.email_verification_sent_at)
    
    def test_verification_with_invalid_token(self):
        """Test verification with an invalid token."""
        verification_url = reverse('verify-email',
                                   kwargs={'user_id': self.user.user_id, 'token': 'invalid-token'})
        response = self.client.get(verification_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'Invalid verification link.')
        
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(self.user.email_verification_token, self.verification_token)
    
    def test_verification_with_nonexistent_user(self):
        """Test verification with a non-existent user ID."""
        verification_url = reverse('verify-email', kwargs={'user_id': 9999, 'token': 'some-token'})
        response = self.client.get(verification_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_verification_already_verified(self):
        """Test verification for an already verified email."""
        self.user.is_active = True
        self.user.email_verification_token = None
        self.user.email_verified = True
        self.user.save()
        
        verification_url = reverse('verify-email',
                                   kwargs={'user_id': self.user.user_id, 'token': 'any-token'})
        response = self.client.get(verification_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')
        self.assertEqual(response.data['message'], 'Invalid verification link.')

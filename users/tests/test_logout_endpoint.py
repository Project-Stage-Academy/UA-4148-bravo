from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework import status

User = get_user_model()

class JWTLogoutTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user', password='test_password123')
        self.login_url = '/api/users/auth/jwt/create/'
        self.logout_url = '/api/users/auth/jwt/logout/'
        self.refresh_url = '/api/users/auth/jwt/refresh/'

        # Get tokens
        response = self.client.post(self.login_url, {
            'username': 'test_user',
            'password': 'test_password123'
        })
        self.refresh_token = response.data['refresh']
        self.access_token = response.data['access']

    def test_logout_blacklists_refresh_token(self):
        response = self.client.post(self.logout_url, {
            'refresh': self.refresh_token
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = OutstandingToken.objects.get(token=self.refresh_token)
        self.assertTrue(BlacklistedToken.objects.filter(token=token).exists())

    def test_blacklisted_token_cannot_be_used(self):
        self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')

        response = self.client.post(self.refresh_url, {
            'refresh': self.refresh_token
        }, format='json')

        self.assertEqual(response.status_code, 401)
        self.assertIn('token is blacklisted', str(response.data).lower())

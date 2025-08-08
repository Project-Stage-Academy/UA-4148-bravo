from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserRole, User


class JWTLogoutTest(APITestCase):
    def setUp(self):
        role = UserRole.objects.get(role=UserRole.Role.USER)
        self.user = User.objects.create_user(
            email='test_user@example.com',
            password='test_password123',
            first_name='Api',
            last_name='Startup',
            role=role,
        )
        self.login_url = '/api/v1/users/login/'
        self.logout_url = '/api/v1/users/auth/jwt/logout/'
        self.refresh_url = '/api/v1/users/auth/jwt/refresh/'

        # Get tokens
        response = self.client.post(self.login_url, {
            'email': 'test_user@example.com',
            'password': 'test_password123'
        })
        print(response.status_code, response.content)
        self.refresh_token = response.data['refresh']
        self.access_token = response.data['access']

    def test_logout_blacklists_refresh_token(self):
        refresh = RefreshToken(self.refresh_token)
        jti = refresh['jti']
        token = OutstandingToken.objects.get(jti=jti)

        response = self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue(BlacklistedToken.objects.filter(token=token).exists())

    def test_blacklisted_token_cannot_be_used(self):
        self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')

        response = self.client.post(self.refresh_url, {
            'refresh': self.refresh_token
        }, format='json')

        self.assertEqual(response.status_code, 401)
        self.assertIn('token is blacklisted', str(response.data).lower())

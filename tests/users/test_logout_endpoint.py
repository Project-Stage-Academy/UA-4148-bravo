import json
from django.test import TestCase
from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import UserRole, User


class JWTLogoutTest(TestCase):
    """
    Test suite for verifying JWT logout functionality with token blacklisting.
    Ensures that refresh tokens are blacklisted on logout and cannot be reused.
    """

    def setUp(self):
        """
        Create a test user, log in to obtain access and refresh tokens,
        and prepare URLs for login, logout, and refresh endpoints.
        """
        role = UserRole.objects.get(role=UserRole.Role.USER)
        self.user = User.objects.create_user(
            email='test_user@example.com',
            password='test_password123',
            first_name='Api',
            last_name='Startup',
            role=role,
            is_active=True
        )
        self.login_url = '/api/v1/auth/jwt/create/'
        self.logout_url = '/api/v1/auth/jwt/logout/'
        self.refresh_url = '/api/v1/auth/jwt/refresh/'

        response = self.client.post(
            self.login_url,
            data=json.dumps({
                'email': self.user.email,
                'password': 'test_password123'
            }),
            content_type='application/json'
        )

        assert response.status_code == 200, f"Login failed: {response.content}"
        assert response.headers['Content-Type'] == 'application/json'

        self.refresh_token = response.data['refresh']
        self.access_token = response.data['access']

    def tearDown(self):
        """
        Cleans up tokens after each test to avoid DB pollution.
        """
        RefreshToken(self.refresh_token).blacklist()
        OutstandingToken.objects.filter(user=self.user).delete()
        BlacklistedToken.objects.filter(token__user=self.user).delete()

    def test_logout_blacklists_refresh_token(self):
        """
        Ensure that logging out blacklists the refresh token.
        The blacklisted token should appear in the BlacklistedToken table.
        """
        refresh = RefreshToken(self.refresh_token)
        jti = refresh['jti']

        try:
            token = OutstandingToken.objects.get(jti=jti)
        except OutstandingToken.DoesNotExist:
            self.fail(f"Outstanding token with jti={jti} not found")

        response = self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertIn('success', str(response.data).lower())

        blacklisted = BlacklistedToken.objects.filter(token=token)
        self.assertEqual(blacklisted.count(), 1)

    def test_blacklisted_token_cannot_be_used(self):
        """
        Ensure that a blacklisted refresh token cannot be used to get a new access token.
        The refresh endpoint should return a 401 Unauthorized response.
        """
        self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')

        response = self.client.post(self.refresh_url, {
            'refresh': self.refresh_token
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.headers['Content-Type'], 'application/json')

        error_detail = response.data.get('detail', '').lower()
        self.assertIn('blacklisted', error_detail)

    def test_logout_twice_does_not_duplicate_blacklist(self):
        """
        Logging out twice should not create duplicate blacklist entries.
        """
        refresh = RefreshToken(self.refresh_token)
        jti = refresh['jti']

        try:
            token = OutstandingToken.objects.get(jti=jti)
        except OutstandingToken.DoesNotExist:
            self.fail(f"Outstanding token with jti={jti} not found")

        response1 = self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        blacklisted = BlacklistedToken.objects.filter(token=token)
        self.assertEqual(blacklisted.count(), 1)


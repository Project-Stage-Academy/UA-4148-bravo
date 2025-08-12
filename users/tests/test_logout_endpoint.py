from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserRole, User
from users.tests.test_setup import BaseUserTestCase


class JWTLogoutTest(BaseUserTestCase):
    def setUp(self):
        """
        Creates a test user and retrieves access/refresh tokens via login.
        """
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

        response = self.client.post(self.login_url, {
            'email': self.user.email,
            'password': 'test_password123'
        })

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
        Should blacklist the refresh token upon logout.
        Also verifies response body and avoids duplicate blacklisting.
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

        # Check response body contains confirmation message
        self.assertIn('success', str(response.data).lower())

        # Ensure token is blacklisted exactly once
        blacklisted = BlacklistedToken.objects.filter(token=token)
        self.assertEqual(blacklisted.count(), 1)

    def test_blacklisted_token_cannot_be_used(self):
        """
        Should reject blacklisted refresh token when trying to refresh access.
        """
        # Logout to blacklist the token
        self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')

        # Attempt to use the blacklisted token
        response = self.client.post(self.refresh_url, {
            'refresh': self.refresh_token
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.headers['Content-Type'], 'application/json')

        # Use .get('detail') for robust error checking
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

        # First logout
        response1 = self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Second logout (should not fail or duplicate)
        response2 = self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # Ensure only one blacklist entry exists
        blacklisted = BlacklistedToken.objects.filter(token=token)
        self.assertEqual(blacklisted.count(), 1)


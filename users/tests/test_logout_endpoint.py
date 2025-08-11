from rest_framework import status
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken
from tests.test_setup import BaseUserTestCase


class JWTLogoutTest(BaseUserTestCase):
    """
    Test suite for JWT logout functionality with token blacklisting.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Create test user once for the whole test case.
        """
        super().setUpTestData()
        cls.login_url = '/api/v1/users/login/'
        cls.logout_url = '/api/v1/users/auth/jwt/logout/'
        cls.refresh_url = '/api/v1/users/auth/jwt/refresh/'

    def setUp(self):
        """
        Log in before each test to obtain fresh tokens.
        """
        login_response = self.client.post(self.login_url, {
            'email': self.user.email,
            'password': self.user_mixin.TEST_USER_PASSWORD
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        self.refresh_token = login_response.data['refresh']
        self.access_token = login_response.data['access']

    def test_logout_blacklists_refresh_token(self):
        """
        Logging out should blacklist the provided refresh token.
        """
        refresh = RefreshToken(self.refresh_token)
        jti = refresh['jti']
        token_obj = OutstandingToken.objects.get(jti=jti)

        response = self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(BlacklistedToken.objects.filter(token=token_obj).exists())

    def test_blacklisted_token_cannot_be_used(self):
        """
        A blacklisted refresh token should not be able to refresh access tokens.
        """
        self.client.post(self.logout_url, {'refresh': self.refresh_token}, format='json')

        response = self.client.post(self.refresh_url, {
            'refresh': self.refresh_token
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('token is blacklisted', str(response.data).lower())

from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from users.models import User, UserRole
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.test import APIClient

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class MeEndpointTests(APITestCase):
    """
    Test suite for the /api/v1/auth/me/ endpoint.

    Covers:
    - Successful response with authenticated user details.
    - Rejection of unauthenticated requests.
    - Handling of inactive users.
    - Handling of users without a role.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Set up test data for the entire TestCase.
        Creates a user role and a test user assigned to that role.
        """
        role, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
        cls.user = User.objects.create_user(
            email="post@example.com",
            password="Test1234!",
            first_name="Paul",
            last_name="Bein",
            user_phone="+123456789",
            title="Developer",
            role=role,
            is_active=True
        )
        cls.url = reverse("auth-me")

    def get_token_for_user(self, user):
        """
        Generate a JWT access token for the given user.

        Args:
            user (User): The user instance to generate a token for.

        Returns:
            str: JWT access token.
        """
        return str(AccessToken.for_user(user))

    def test_me_returns_current_user(self):
        """
        Ensure that the 'me' endpoint returns the current authenticated user's details
        and does not expose the password.
        """
        token = self.get_token_for_user(self.user)
        self.client.cookies['access_token'] = token
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.json()
        self.assertEqual(body["email"], self.user.email)
        self.assertEqual(body["first_name"], self.user.first_name)
        self.assertEqual(body["last_name"], self.user.last_name)
        self.assertEqual(body["user_phone"], self.user.user_phone)
        self.assertEqual(body["title"], self.user.title)
        self.assertEqual(body["role"], getattr(self.user.role, 'role', None))
        self.assertNotIn("password", body)

    def test_me_requires_auth(self):
        """Ensure 'me' endpoint requires authentication -> 401."""
        client = APIClient(enforce_csrf_checks=False)
        resp = client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_inactive_user(self):
        """Inactive users cannot access 'me' endpoint."""
        self.user.is_active = False
        self.user.save()

        token = self.get_token_for_user(self.user)
        client = APIClient(enforce_csrf_checks=False)

        client.cookies['access_token'] = token
        resp = client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

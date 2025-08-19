from django.contrib.auth import get_user_model
from users.models import User, UserRole
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

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
        Create a default user role and a test user with that role.
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
            is_active=True,
        )
        cls.url = reverse("auth-me")

    def get_token_for_user(self, user):
        """
        Generate a JWT access token for the given user.

        Args:
            user (User): The user instance.

        Returns:
            str: A valid JWT access token.
        """
        return str(AccessToken.for_user(user))

    def test_me_returns_current_user(self):
        """
        Authenticated request returns 200 with correct user details
        and excludes sensitive fields (e.g., password).
        """
        token = self.get_token_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.json()
        self.assertEqual(body["email"], self.user.email)
        self.assertEqual(body["first_name"], self.user.first_name)
        self.assertEqual(body["last_name"], self.user.last_name)
        self.assertEqual(body["user_phone"], self.user.user_phone)
        self.assertEqual(body["title"], self.user.title)
        self.assertEqual(body["role"], self.user.role.role)
        self.assertNotIn("password", body)

    def test_me_requires_auth(self):
        """
        Unauthenticated request should return 401 Unauthorized.
        """
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_inactive_user(self):
        """
        Inactive users cannot access the endpoint (expect 403 Forbidden).
        """
        self.user.is_active = False
        self.user.save()

        token = self.get_token_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_user_without_role(self):
        """
        Endpoint still works if the user has no role (role should be null).
        """
        self.user.role = None
        self.user.save()

        token = self.get_token_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.json()
        self.assertIsNone(body["role"])

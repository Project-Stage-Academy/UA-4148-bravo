from django.contrib.auth import get_user_model
from users.models import User, UserRole
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class MeEndpointTests(APITestCase):
    """
    Test the 'me' endpoint which returns the current authenticated user's details.
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
        Ensure that the 'me' endpoint requires authentication and returns 401 if no token is provided.
        """
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

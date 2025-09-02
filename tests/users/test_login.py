from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIClient
from users.models import UserRole, User


@override_settings(SECURE_SSL_REDIRECT=False)
class AuthLoginTestCase(TestCase):
    """
    TestCase to verify JWT login functionality.

    Covers:
    - Successful login with valid credentials
    - Login with wrong password
    - Login for nonexistent users
    - Login requests with missing required fields
    """

    def setUp(self):
        """Setup test environment by creating a user role and a test user."""
        self.client = APIClient()
        self.role, _ = UserRole.objects.get_or_create(role="user")
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass",
            first_name="Test",
            last_name="User",
            role=self.role,
            is_active=True,
        )

    def test_successful_login(self):
        """User can successfully log in with valid credentials."""
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "testuser@example.com",
            "password": "testpass"
        }, format="json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "Login successful")
        self.assertEqual(data["user_id"], self.user.id)
        self.assertEqual(data["email"], self.user.email)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_login_wrong_password(self):
        """Login attempt with wrong password returns 401 Unauthorized."""
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "testuser@example.com",
            "password": "wrongpass"
        }, format="json")

        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        """Login attempt with an unregistered email returns 401 Unauthorized."""
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "ghost@example.com",
            "password": "nopass"
        }, format="json")

        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        """Login request missing required fields returns 400 Bad Request."""
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "testuser@example.com"
        }, format="json")

        self.assertEqual(response.status_code, 400)

from django.test import Client
from django.test import TestCase
from users.models import UserRole, User


class LoginTestCase(TestCase):
    """
    TestCase to verify user login functionality.
    Covers successful login, login with wrong credentials,
    login attempts for nonexistent users, and requests with missing fields.
    """

    def setUp(self):
        """
        Setup test environment by creating a user role and a test user.
        """
        self.client = Client()
        self.role, _ = UserRole.objects.get_or_create(role="user")
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass",
            first_name="Test",
            last_name="User",
            role=self.role,
            is_active=True
            role=self.role,
            is_active=True
        )

    def test_successful_login(self):
        """
        Test that a user can successfully log in with valid credentials.
        Verifies that the response status is 200 and tokens are returned,
        along with correct user data.
        """
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "testuser@example.com",
            "password": "testpass"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["user_id"], self.user.user_id)
        self.assertEqual(data["email"], self.user.email)

    def test_login_wrong_password(self):
        """
        Test login attempt with a wrong password.
        Verifies that the response status is 401 Unauthorized.
        """
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "testuser@example.com",
            "password": "wrongpass"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        """
        Test login attempt with an email not registered in the system.
        Verifies that the response status is 401 Unauthorized.
        """
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "ghost@example.com",
            "password": "nopass"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        """
        Test login request missing required fields (e.g., missing password).
        Verifies that the response status is 400 Bad Request.
        """
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "testuser@example.com"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 400)

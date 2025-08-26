from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from users.models import UserRole

User = get_user_model()


class AuthLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.role, _ = UserRole.objects.get_or_create(role="user")
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass",
            first_name="Test",
            last_name="User",
            role=self.role,
            is_active=True
        )

    def test_successful_login(self):
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "testuser@example.com",
            "password": "testpass"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["user_id"], self.user.pk)
        self.assertEqual(data["email"], self.user.email)

    def test_login_wrong_password(self):
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "testuser@example.com",
            "password": "wrongpass"
        })
        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "ghost@example.com",
            "password": "nopass"
        })
        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        response = self.client.post("/api/v1/auth/jwt/create/", {
            "email": "testuser@example.com"
        })
        self.assertEqual(response.status_code, 400)

from django.test import Client

from users.models import UserRole, User
from users.tests.test_setup import BaseUserTestCase


class LoginTestCase(BaseUserTestCase):
    def setUp(self):
        self.client = Client()
        self.role, _ = UserRole.objects.get_or_create(role="user")
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass",
            first_name="Test",
            last_name="User",
            role=self.role
        )

    def test_successful_login(self):
        response = self.client.post("/api/v1/users/login/", {
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
        response = self.client.post("/api/v1/users/login/", {
            "email": "testuser@example.com",
            "password": "wrongpass"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        response = self.client.post("/api/v1/users/login/", {
            "email": "ghost@example.com",
            "password": "nopass"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        response = self.client.post("/api/v1/users/login/", {
            "email": "testuser@example.com"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 400)

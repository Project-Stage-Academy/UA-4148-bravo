from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class CustomPasswordResetTests(APITestCase):
    def setUp(self):
        self.user_password = "OldPass123!"
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password=self.user_password
        )
        self.reset_url = "/api/users/reset_password/"
        self.confirm_url = "/api/users/reset_password_confirm/"

    # Tests for CustomPasswordResetView

    def test_reset_password_success(self):
        """Should send reset email if user exists."""
        response = self.client.post(self.reset_url, {"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_reset_password_no_email_provided(self):
        """Should return 400 if email is missing."""
        response = self.client.post(self.reset_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_reset_password_user_not_found(self):
        """Should return 404 if user does not exist."""
        response = self.client.post(self.reset_url, {"email": "nonexistent@example.com"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("email", response.data)

    # Tests for CustomPasswordResetConfirmView

    def test_reset_password_confirm_success(self):
        """Should reset password if token and uid are valid."""
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        new_password = "NewPass123!"

        response = self.client.post(self.confirm_url, {
            "uid": uid,
            "token": token,
            "new_password": new_password
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    def test_reset_password_confirm_missing_fields(self):
        """Should return 400 if required fields are missing."""
        response = self.client.post(self.confirm_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_reset_password_confirm_invalid_uid(self):
        """Should return 400 if UID is invalid."""
        token = default_token_generator.make_token(self.user)
        response = self.client.post(self.confirm_url, {
            "uid": "invalid",
            "token": token,
            "new_password": "NewPass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("uid", response.data)

    def test_reset_password_confirm_invalid_token(self):
        """Should return 400 if token is invalid."""
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.post(self.confirm_url, {
            "uid": uid,
            "token": "invalid-token",
            "new_password": "NewPass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)

    def test_reset_password_confirm_invalid_password(self):
        """Should return 400 if password does not meet validators."""
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.post(self.confirm_url, {
            "uid": uid,
            "token": token,
            "new_password": "123"  # invalid password
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

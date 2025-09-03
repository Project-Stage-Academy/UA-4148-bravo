from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test.utils import override_settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class CustomPasswordResetTests(APITestCase):
    """
    Integration tests for the custom password reset and password reset confirmation API views.
    """
    def setUp(self):
        """
        Set up a test user and define the URLs used in password reset flows.
        """
        self.user_password = "OldPass123!"
        self.user = User.objects.create_user(
            email="test@example.com",
            password=self.user_password
        )
        self.reset_url = "/api/v1/auth/password/reset/"
        self.confirm_url = "/api/v1/auth/password/reset/confirm/"

    # Tests for CustomPasswordResetView

    def test_reset_password_success(self):
        """
        Test that the reset password endpoint returns 200 OK when a valid email is provided.
        """
        response = self.client.post(self.reset_url, {"email": self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

    def test_reset_password_no_email_provided(self):
        """
        Test that the reset password endpoint returns 400 BAD REQUEST when no email is provided.
        """
        response = self.client.post(self.reset_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_reset_password_user_not_found(self):
        """
        Test that the reset password endpoint returns 404 NOT FOUND when the email is not registered.
        """
        response = self.client.post(self.reset_url, {"email": "nonexistent@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    # Tests for CustomPasswordResetConfirmView

    def test_reset_password_confirm_success(self):
        """
        Test that a user can reset their password when providing a valid UID, token, and password.
        """
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
        """
        Test that the confirmation endpoint returns 400 BAD REQUEST when required fields are missing.
        """
        response = self.client.post(self.confirm_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("uid", response.data)
        self.assertIn("token", response.data)
        self.assertIn("new_password", response.data)

    def test_reset_password_confirm_invalid_uid(self):
        """
        Test that the confirmation endpoint returns 400 BAD REQUEST when the UID is invalid.
        """
        token = default_token_generator.make_token(self.user)
        response = self.client.post(self.confirm_url, {
            "uid": "invalid",
            "token": token,
            "new_password": "NewPass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("uid", response.data)

    def test_reset_password_confirm_invalid_token(self):
        """
        Test that the confirmation endpoint returns 400 BAD REQUEST when the token is invalid.
        """
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.post(self.confirm_url, {
            "uid": uid,
            "token": "invalid-token",
            "new_password": "NewPass123!"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)

    def test_reset_password_confirm_invalid_password(self):
        """
        Test that the confirmation endpoint returns 400 BAD REQUEST when the new password is too weak or invalid.
        """
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.post(self.confirm_url, {
            "uid": uid,
            "token": token,
            "new_password": "123"  # invalid password
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

    def test_reset_password_confirm_custom_validator(self):
        """
        Test that the custom password validator correctly rejects weak passwords.
        Each test case is run as a subTest with its own password violation type.
        """
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        invalid_passwords = {
            "missing_uppercase": "password123!",
            "missing_lowercase": "PASSWORD123!",
            "missing_number": "Password!",
            "missing_special": "Password123",
            "too_simple": "pass"
        }

        for case, invalid_password in invalid_passwords.items():
            with self.subTest(msg=f"Case: {case}"):
                response = self.client.post(self.confirm_url, {
                    "uid": uid,
                    "token": token,
                    "new_password": invalid_password
                })

                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                    msg=f"Expected 400 for case '{case}', got {response.status_code}."
                )
                self.assertIn(
                    "new_password",
                    response.data,
                    msg=f"Expected 'new_password' error in case '{case}', got {response.data}."
                )

    def test_reset_password_confirm_valid_password(self):
        """
        Test that the confirmation endpoint accepts a valid password and updates the user's password.
        """
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        valid_password = "Valid123!"

        response = self.client.post(self.confirm_url, {
            "uid": uid,
            "token": token,
            "new_password": valid_password
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(valid_password))

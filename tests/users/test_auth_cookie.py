from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, UserRole
import os
from dotenv import load_dotenv

load_dotenv()
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


class AuthCookieTests(APITestCase):
    """
    Test suite for JWT authentication using HTTPOnly cookies and CSRF protection.

    This includes tests for:
        - CSRF token retrieval
        - Login and setting of secure HTTPOnly refresh token cookie
        - Access token retrieval
        - Refreshing access token using cookie
        - Logout and deletion of refresh cookie
        - Accessing protected endpoints with access token
    """

    def setUp(self):
        """Create a test user and configure the APIClient with CSRF checks enabled."""
        role_user, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
        self.user = User.objects.create_user(
            email="test@example.com",
            password=TEST_USER_PASSWORD,
            first_name="Test",
            last_name="User",
            role=role_user,
            is_active=True
        )
        self.client = APIClient(enforce_csrf_checks=True)
        self.csrf_url = reverse("csrf-init")
        self.login_url = reverse("jwt-create")
        self.refresh_url = reverse("jwt-refresh")
        self.logout_url = reverse("jwt-logout")
        self.protected_url = reverse("auth-me")

    def _get_csrf_token(self):
        """
        Retrieve a valid CSRF token from the server.

        Returns:
            str: The CSRF token value.
        """
        response = self.client.get(self.csrf_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.cookies["csrftoken"].value

    def test_login_sets_http_only_cookie(self):
        """
        Test that logging in sets the refresh token as a secure, HTTPOnly cookie
        and returns an access token in the response body.
        """
        csrf_token = self._get_csrf_token()
        response = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": TEST_USER_PASSWORD},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh_token", response.cookies)
        cookie = response.cookies["refresh_token"]
        self.assertTrue(cookie["httponly"])
        self.assertTrue(cookie["secure"])

    def test_refresh_works_with_cookie(self):
        """
        Test that the refresh endpoint returns a new access token when the refresh
        token cookie is present.
        """
        csrf_token = self._get_csrf_token()
        self.client.post(
            self.login_url,
            {"email": self.user.email, "password": TEST_USER_PASSWORD},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        response = self.client.post(
            self.refresh_url,
            {},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_fails_without_cookie(self):
        """
        Test that the refresh endpoint returns 401 Unauthorized if the refresh
        token cookie is missing.
        """
        csrf_token = self._get_csrf_token()
        response = self.client.post(
            self.refresh_url,
            {},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_deletes_cookie(self):
        """
        Ensure that logging out clears the refresh token cookie on the client
        and returns HTTP 205 RESET CONTENT.
        """
        csrf_token = self._get_csrf_token()
        self.client.post(
            self.login_url,
            {"email": self.user.email, "password": TEST_USER_PASSWORD},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        response = self.client.post(
            self.logout_url,
            {},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertIn("refresh_token", response.cookies)
        cookie = response.cookies["refresh_token"]
        self.assertEqual(cookie.value, "")

    def test_logout_without_cookie_still_succeeds(self):
        """
        Ensure that logging out without a refresh token cookie still succeeds
        and clears any existing refresh token cookie on the client.
        """
        csrf_token = self._get_csrf_token()
        response = self.client.post(
            self.logout_url,
            {},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertIn("refresh_token", response.cookies)
        cookie = response.cookies["refresh_token"]
        self.assertEqual(cookie.value, "")

    def test_logout_with_invalid_token_still_succeeds(self):
        """
        Ensure that logging out with an invalid refresh token still succeeds
        and clears the refresh token cookie.
        """
        csrf_token = self._get_csrf_token()
        self.client.cookies["refresh_token"] = "invalidtoken123"
        response = self.client.post(
            self.logout_url,
            {},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertIn("refresh_token", response.cookies)
        cookie = response.cookies["refresh_token"]
        self.assertEqual(cookie.value, "")

    def test_access_token_works_for_protected_endpoint(self):
        """
        Test that an access token obtained from login allows access to a protected
        endpoint.
        """
        csrf_token = self._get_csrf_token()
        login_resp = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": TEST_USER_PASSWORD},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        access_token = login_resp.data["access"]
        protected_url = reverse("auth-me")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_endpoint_without_token(self):
        """
        Ensure accessing a protected endpoint without an Authorization header
        returns 401 Unauthorized.
        """
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_endpoint_with_invalid_token(self):
        """
        Ensure accessing a protected endpoint with an invalid access token
        returns 401 Unauthorized.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalidtoken123")
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_fails_with_invalid_cookie(self):
        """
        Ensure the refresh endpoint returns 401 Unauthorized if the refresh
        token cookie is invalid or tampered with.
        """
        csrf_token = self._get_csrf_token()
        self.client.cookies["refresh_token"] = "invalidtoken123"
        response = self.client.post(
            self.refresh_url,
            {},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

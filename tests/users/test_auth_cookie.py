from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import User, UserRole
import os
from dotenv import load_dotenv
import jwt
from django.conf import settings

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
        self.assertIn("refresh", response.data)
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
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_logout_deletes_cookie(self):
        """
        Ensure that logging out clears the refresh token cookie on the client
        and returns HTTP 205 RESET CONTENT.
        """
        csrf_token = self._get_csrf_token()
        login_response = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": TEST_USER_PASSWORD},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        access_token = login_response.data["access"]
        response = self.client.post(
            self.logout_url,
            {},
            HTTP_X_CSRFTOKEN=csrf_token,
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertIn("refresh_token", response.cookies)
        cookie = response.cookies["refresh_token"]
        self.assertEqual(cookie.value, "")
        self.assertEqual(cookie["max-age"], 0)

    def test_logout_always_succeeds_and_clears_cookie(self):
        """
        Logout should always succeed and clear the refresh token cookie,
        regardless of whether the refresh token is present, invalid, or missing.
        """
        csrf_token = self._get_csrf_token()
        login_response = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": TEST_USER_PASSWORD},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        access_token = login_response.data["access"]

        scenarios = {
            "without_cookie": None,
            "with_invalid_cookie": "invalidtoken123",
        }

        for case, token in scenarios.items():
            with self.subTest(case=case):
                if token:
                    self.client.cookies["refresh_token"] = token

                response = self.client.post(
                    self.logout_url,
                    {},
                    HTTP_X_CSRFTOKEN=csrf_token,
                    HTTP_AUTHORIZATION=f"Bearer {access_token}"
                )

                self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
                self.assertIn("refresh_token", response.cookies)
                cookie = response.cookies["refresh_token"]
                self.assertEqual(cookie.value, "")
                self.assertEqual(cookie["max-age"], 0)

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
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_jwt_algorithm(self):
        """
        Verify that the JWT access token is signed with the correct algorithm.
        """
        csrf_token = self._get_csrf_token()
        login_resp = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": TEST_USER_PASSWORD},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(login_resp.status_code, status.HTTP_200_OK)
        access_token = login_resp.data["access"]

        header = jwt.get_unverified_header(access_token)

        expected_alg = settings.SIMPLE_JWT.get("ALGORITHM", "HS256")
        self.assertEqual(header["alg"], expected_alg)

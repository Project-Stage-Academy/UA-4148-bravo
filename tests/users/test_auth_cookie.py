from django.test.utils import override_settings
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


@override_settings(SECURE_SSL_REDIRECT=False)
class AuthCookieTests(APITestCase):
    """
    Test suite for JWT authentication using HTTPOnly cookies and CSRF protection.

    This suite tests:
        - CSRF token retrieval
        - Login and setting of secure HTTPOnly cookies for access and refresh tokens
        - Refreshing access token using refresh cookie
        - Logout and clearing cookies
        - Accessing protected endpoints with valid/invalid tokens
        - Correct JWT signing algorithm
    """

    def setUp(self):
        """
        Create a test user and configure the APIClient with CSRF checks enabled.
        """
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
        self.csrf_url = reverse("csrf_init")
        self.login_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")
        self.logout_url = reverse("logout")
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
        Ensure that logging in sets access_token and refresh_token
        as HTTPOnly and secure cookies. Tokens should not appear in response body.
        """
        csrf_token = self._get_csrf_token()
        response = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": TEST_USER_PASSWORD},
            HTTP_X_CSRFTOKEN=csrf_token,
            secure=True,
            HTTP_REFERER='https://testserver/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        for key in ["access_token", "refresh_token"]:
            self.assertIn(key, response.cookies)
            cookie = response.cookies[key]
            self.assertTrue(cookie["httponly"])
            self.assertTrue(cookie["secure"])

    def test_refresh_works_with_cookie(self):
        """
        Test that the refresh endpoint issues a new access_token cookie
        when a valid refresh_token cookie is present.
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
        self.assertIn("access_token", response.cookies)

    def test_refresh_fails_without_cookie(self):
        """
        Test that refresh endpoint returns 404 if refresh_token cookie is missing.
        """
        csrf_token = self._get_csrf_token()
        response = self.client.post(
            self.refresh_url,
            {},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_refresh_fails_with_invalid_cookie(self):
        """
        Test that refresh endpoint returns 205 RESET CONTENT if refresh_token is invalid.
        """
        csrf_token = self._get_csrf_token()
        self.client.cookies["refresh_token"] = "invalidtoken123"
        response = self.client.post(
            self.refresh_url,
            {},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_logout_clears_cookies(self):
        """
        Test that logout clears both access_token and refresh_token cookies
        and returns HTTP 200 OK.
        """
        csrf_token = self._get_csrf_token()
        login_response = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": TEST_USER_PASSWORD},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        access_token = login_response.cookies["access_token"].value
        response = self.client.post(
            self.logout_url,
            {},
            HTTP_X_CSRFTOKEN=csrf_token,
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ["access_token", "refresh_token"]:
            cookie = response.cookies[key]
            self.assertEqual(cookie.value, "")
            self.assertEqual(cookie["max-age"], 0)

    def test_access_token_allows_protected_endpoint(self):
        """
        Ensure that an access_token obtained from login
        allows access to a protected endpoint.
        """
        csrf_token = self._get_csrf_token()
        login_resp = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": TEST_USER_PASSWORD},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        access_token = login_resp.cookies["access_token"].value

        self.client.cookies["access_token"] = access_token
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_protected_endpoint_without_token(self):
        """Accessing protected endpoint without any token should return 401"""
        client = APIClient(enforce_csrf_checks=False)
        response = client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_protected_endpoint_with_invalid_token(self):
        """Accessing protected endpoint with invalid token returns 401"""
        client = APIClient(enforce_csrf_checks=False)
        client.cookies["access_token"] = "invalidtoken123"
        response = client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_jwt_algorithm(self):
        """
        Verify that the JWT access_token is signed with the correct algorithm
        defined in SIMPLE_JWT settings.
        """
        csrf_token = self._get_csrf_token()
        login_resp = self.client.post(
            self.login_url,
            {"email": self.user.email, "password": TEST_USER_PASSWORD},
            HTTP_X_CSRFTOKEN=csrf_token
        )
        access_token = login_resp.cookies["access_token"].value
        header = jwt.get_unverified_header(access_token)
        expected_alg = settings.SIMPLE_JWT.get("ALGORITHM", "HS256")
        self.assertEqual(header["alg"], expected_alg)

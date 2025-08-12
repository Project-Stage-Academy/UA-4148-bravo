from tests.test_base import DisableSignalMixinUser, BaseAPITestCase
from tests.input_data import TEST_USER_PASSWORD
from django.contrib.auth import authenticate

class LoginTestCase(DisableSignalMixinUser, BaseAPITestCase):
    """
    TestCase for verifying user login API functionality.
    Uses UserMixin to create a users user with a password from environment variables.
    """

    def test_password_debug(self):
        user = authenticate(email="testuser@example.com", password=TEST_USER_PASSWORD)
        assert user is not None, "Authentication failed in test setup"

    def test_successful_login(self):
        """
        Test successful login with valid credentials.
        Checks that the response status is 200,
        and that the access and refresh tokens are included in the response,
        along with correct user_id and email.
        """
        response = self.client.post("/api/v1/users/login/", {
            "email": "testuser@example.com",
            "password": TEST_USER_PASSWORD
        }, content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["user_id"], self.user.user_id)
        self.assertEqual(data["email"], self.user.email)

    def test_login_wrong_password(self):
        """
        Test login attempt with an incorrect password.
        Expects a 401 Unauthorized response.
        """
        response = self.client.post("/api/v1/users/login/", {
            "email": "testuser@example.com",
            "password": "wrongpass"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 401)

    def test_login_nonexistent_user(self):
        """
        Test login attempt with a non-existent user.
        Expects a 401 Unauthorized response.
        """
        response = self.client.post("/api/v1/users/login/", {
            "email": "ghost@example.com",
            "password": "nopass"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 401)

    def test_login_missing_fields(self):
        """
        Test login attempt with missing required fields.
        Expects a 400 Bad Request response.
        """
        response = self.client.post("/api/v1/users/login/", {
            "email": "testuser@example.com"
        }, content_type="application/json")

        self.assertEqual(response.status_code, 400)

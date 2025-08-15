from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class MeEndpointTests(APITestCase):
    def setUp(self):
        self.url = reverse("/api/v1/auth/me/")

    def test_me_returns_current_user(self):
        user = User.objects.create_user(
            email="post@example.com",
            password="Test1234!",
            first_name="Paul",
            last_name="Bein",
            user_phone = "+123456789",
            title="Developer",
            role="user"
        )
        token = str(AccessToken.for_user(user))

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = self.client.get(self.url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        body = resp.json()
        self.assertEqual(body["email"], "post@example.com")
        self.assertEqual(body["first_name"], "Paul")
        self.assertEqual(body["last_name"], "Bein")
        self.assertEqual(body["user_phone"], "+123456789")
        self.assertEqual(body["title"], "Developer")
        self.assertEqual(body["role"], "user")
        self.assertNotIn("password", body)

    def test_me_requires_auth(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
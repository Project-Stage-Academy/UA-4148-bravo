from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from startups.models import Startup
from investors.models import ViewedStartup

User = get_user_model()


class RecentlyViewedStartupTests(APITestCase):
    def setUp(self):
        # Create investor user
        self.investor = User.objects.create_user(
            email="investor@example.com",
            password="testpass123",
            is_investor=True
        )
        self.client.login(email="investor@example.com", password="testpass123")

        # Create startup
        self.startup = Startup.objects.create(
            name="Test Startup",
            description="Some description"
        )

    def test_record_viewed_startup(self):
        """Test that a viewed startup is recorded in history"""
        url = reverse("recently-viewed-list")
        response = self.client.post(url, {"startup": self.startup.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            ViewedStartup.objects.filter(investor=self.investor, startup=self.startup).exists()
        )

    def test_list_recently_viewed(self):
        """Test retrieving list of recently viewed startups"""
        ViewedStartup.objects.create(investor=self.investor, startup=self.startup)
        url = reverse("recently-viewed-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["startup"]["id"], self.startup.id)

    def test_clear_history(self):
        """Test that history can be cleared"""
        ViewedStartup.objects.create(investor=self.investor, startup=self.startup)
        url = reverse("recently-viewed-clear-history")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ViewedStartup.objects.filter(investor=self.investor).exists()
        )

    def test_permissions(self):
        """Test that non-investors cannot access endpoints"""
        self.client.logout()
        non_investor = User.objects.create_user(
            email="user@example.com", password="testpass123", is_investor=False
        )
        self.client.login(email="user@example.com", password="testpass123")

        url = reverse("recently-viewed-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

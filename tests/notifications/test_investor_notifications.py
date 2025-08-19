# tests/notifications/test_investor_notifications.py
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from investors.models import Investor, SavedStartup
from notifications.models import Notification
from startups.models import Startup, Industry, Location


def _items(response):
    """
    Normalize DRF list responses: if pagination is enabled it returns a dict with "results",
    otherwise it's just a list.
    """
    data = response.json()
    return data["results"] if isinstance(data, dict) and "results" in data else data


class InvestorNotificationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.client = APIClient()

        #reference data
        self.industry = Industry.objects.create(name="IT")
        self.location = Location.objects.create(
            country="US",
            region="CA",
            city="SF",
            postal_code="94105",
        )

        #investor + user
        self.investor_user = User.objects.create_user(
            email="investor@example.com",
            password="Pass123!",
            first_name="Ivan",
        )
        self.investor = Investor.objects.create(
            user=self.investor_user,
            company_name="API Capital",
            industry=self.industry,
            location=self.location,
            founded_year=2020,
            stage="mvp",
            fund_size="1000000.00",
        )

        #startup + owner user
        self.startup_user = User.objects.create_user(
            email="owner@example.com",
            password="Pass123!",
            first_name="Owner",
        )
        self.startup = Startup.objects.create(
            user=self.startup_user,
            company_name="StarUp",
            industry=self.industry,
            location=self.location,
            founded_year=2021,
            stage="mvp",
            email="startup@example.com",  # Startup.email is unique
        )

        #another regular user (not owner)
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="Pass123!",
        )

    def test_follow_creates_notification(self):
        """When investor follows a startup → notification is created."""
        self.assertEqual(Notification.objects.count(), 0)

        SavedStartup.objects.create(investor=self.investor, startup=self.startup)

        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.investor, self.investor)
        self.assertEqual(notif.startup, self.startup)
        self.assertEqual(notif.type, Notification.Type.FOLLOW)
        self.assertFalse(notif.is_read)

    def test_notification_visible_in_api(self):
        """Startup owner sees notification in API list."""
        SavedStartup.objects.create(investor=self.investor, startup=self.startup)

        self.client.force_authenticate(user=self.startup_user)
        url = reverse("notifications-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        items = _items(res)
        self.assertTrue(any(n.get("type") == "follow" for n in items))

    def test_startup_owner_can_mark_as_read(self):
        """Startup owner can mark notification as read."""
        SavedStartup.objects.create(investor=self.investor, startup=self.startup)
        notif = Notification.objects.get(startup=self.startup, type=Notification.Type.FOLLOW)

        self.client.force_authenticate(user=self.startup_user)
        url = reverse("notifications-read", kwargs={"pk": notif.id})
        res = self.client.patch(url)
        self.assertIn(res.status_code, (200, 204))

        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_non_owner_cannot_mark_as_read(self):
        """Other user cannot mark someone else's notification as read."""
        SavedStartup.objects.create(investor=self.investor, startup=self.startup)
        notif = Notification.objects.get(startup=self.startup, type=Notification.Type.FOLLOW)

        self.client.force_authenticate(user=self.other_user)
        url = reverse("notifications-read", kwargs={"pk": notif.id})
        res = self.client.patch(url)
        self.assertEqual(res.status_code, 403)

        notif.refresh_from_db()
        self.assertFalse(notif.is_read)

    def test_requires_authentication(self):
        """Unauthenticated user gets 401 when accessing notifications."""
        SavedStartup.objects.create(investor=self.investor, startup=self.startup)
        url = reverse("notifications-list")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 401)

    def test_only_owner_sees_notification(self):
        """Only startup owner can see their notifications."""
        SavedStartup.objects.create(investor=self.investor, startup=self.startup)

        self.client.force_authenticate(user=self.startup_user)
        res1 = self.client.get(reverse("notifications-list"))
        self.assertEqual(res1.status_code, 200)
        items1 = _items(res1)
        self.assertGreaterEqual(len(items1), 1)

        self.client.force_authenticate(user=self.other_user)
        res2 = self.client.get(reverse("notifications-list"))
        self.assertEqual(res2.status_code, 200)
        items2 = _items(res2)
        self.assertEqual(len(items2), 0)

    def test_notifications_ordering(self):
        """Newer notifications appear first in API list."""
        User = get_user_model()
        owner2 = User.objects.create_user(email="owner2@example.com", password="Pass123!")
        startup2 = Startup.objects.create(
            user=owner2,
            company_name="NextStar",
            industry=self.industry,
            location=self.location,
            founded_year=2022,
            stage="seed",
            email="nextstar@example.com",
        )

        SavedStartup.objects.create(investor=self.investor, startup=self.startup)
        SavedStartup.objects.create(investor=self.investor, startup=startup2)

        self.client.force_authenticate(user=self.startup_user)
        res = self.client.get(reverse("notifications-list"))
        self.assertEqual(res.status_code, 200)
        items = _items(res)

        for i in range(len(items) - 1):
            self.assertGreaterEqual(
                items[i]["created_at"], items[i + 1]["created_at"],
                "Notifications are not ordered by created_at desc"
            )

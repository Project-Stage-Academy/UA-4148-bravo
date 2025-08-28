from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from django.urls import reverse
from users.models import User, UserRole
from investors.models import ViewedStartup, Startup

class ViewedStartupTests(APITestCase):
    """
    Test suite for the ViewedStartup API endpoints:
    - List viewed startups
    - Create a viewed startup record
    - Clear viewed startups history
    """

    def setUp(self):
        """
        Set up an investor user, multiple startups, and corresponding
        viewed startup records with different timestamps.
        """
        # Create roles
        self.investor_role = UserRole.objects.create(role="investor")

        # Create an investor user
        self.investor = User.objects.create_user(
            email="investor@example.com",
            password="strongpass123",
            first_name="Investor",
            last_name="Test",
            role=self.investor_role
        )
        self.client.force_authenticate(user=self.investor)

        # Create multiple startups
        self.startups = [Startup.objects.create(company_name=f"Startup {i}") for i in range(5)]

        # Create ViewedStartup records
        now = timezone.now()
        for i, startup in enumerate(self.startups):
            ViewedStartup.objects.create(
                user=self.investor,
                startup=startup,
                viewed_at=now - timedelta(minutes=i)
            )

        # URLs
        self.list_url = reverse("viewed-startups-list")
        self.clear_url = reverse("viewed-startups-clear")
        self.create_url = lambda startup_id: reverse("viewed-startup-create", args=[startup_id])

    def test_list_viewed_startups_ordered(self):
        """
        Ensure the list of viewed startups is ordered by viewed_at
        in descending order.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]

        # First item is the most recently viewed
        self.assertEqual(results[0]["company_name"], "Startup 0")
        # Last item on default page
        self.assertEqual(results[-1]["company_name"], "Startup 4")

    def test_list_pagination_limit(self):
        """
        Ensure the `limit` query parameter correctly limits the number
        of results returned.
        """
        response = self.client.get(self.list_url + "?limit=2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_create_viewed_startup(self):
        """
        Ensure that posting to the viewed startup endpoint creates
        a new record or updates the existing one.
        """
        startup = Startup.objects.create(company_name="New Startup")
        response = self.client.post(self.create_url(startup.id))
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(data["company_name"], "New Startup")
        self.assertIn("viewed_at", data)

        # Posting again should update the timestamp
        old_viewed_at = ViewedStartup.objects.get(user=self.investor, startup=startup).viewed_at
        response = self.client.post(self.create_url(startup.id))
        new_viewed_at = ViewedStartup.objects.get(user=self.investor, startup=startup).viewed_at
        self.assertGreater(new_viewed_at, old_viewed_at)

    def test_clear_viewed_startups(self):
        """
        Ensure the DELETE endpoint clears all viewed startup history
        for the authenticated investor.
        """
        response = self.client.delete(self.clear_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ViewedStartup.objects.filter(user=self.investor).count(), 0)
        self.assertIn("deleted_count", response.data)
        self.assertEqual(response.data["deleted_count"], 5)

    def test_only_investor_can_access_endpoints(self):
        """
        Ensure that only users with the investor role can access the
        list, create, and clear endpoints.
        """
        # Create a non-investor user
        user_role = UserRole.objects.create(role="user")
        normal_user = User.objects.create_user(
            email="user@example.com",
            password="strongpass123",
            first_name="Normal",
            last_name="User",
            role=user_role
        )
        self.client.force_authenticate(user=normal_user)

        # List endpoint
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 403)

        # Create endpoint
        startup = Startup.objects.create(company_name="Forbidden Startup")
        response = self.client.post(self.create_url(startup.id))
        self.assertEqual(response.status_code, 403)

        # Clear endpoint
        response = self.client.delete(self.clear_url)
        self.assertEqual(response.status_code, 403)

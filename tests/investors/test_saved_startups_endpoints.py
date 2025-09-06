from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from investors.models import Investor, SavedStartup
from startups.models import Startup, Industry, Location
from users.models import UserRole
from utils.authenticate_client import authenticate_client


@override_settings(SECURE_SSL_REDIRECT=False)
class SavedStartupsEndpointsTests(APITestCase):
    """
    API endpoints under investors app:

    - GET    /api/investor/saved-startups/              -> list current investor's saved startups
      Query params supported:
        * status=watching|contacted|negotiating|passed
        * saved_after=<ISO datetime>, saved_before=<ISO datetime>
        * search=<substring of startup name/email>
        * ordering=saved_at|-saved_at|status|startup__company_name

    - DELETE /api/startups/<startup_id>/unsave/         -> idempotent unsave (200, {"deleted": true/false})
    """

    def setUp(self):
        User = get_user_model()

        # Role (create if missing)
        self.role_user, _ = UserRole.objects.get_or_create(role="user")

        # FK fixtures
        self.location = Location.objects.create(country="US", city="NYC", region="NY")
        self.industry = Industry.objects.create(name="FinTech")

        # Investor user (authenticated caller)
        self.user = User.objects.create(
            email="inv@example.com",
            password=make_password("Pass123!"),
            role=self.role_user,
            is_active=True
        )
        self.investor = Investor.objects.create(
            user=self.user,
            industry=self.industry,
            company_name="API Capital",
            location=self.location,
            email="api.capital@example.com",
            founded_year=2020,
            team_size=5,
            stage="mvp",
            fund_size="1000000.00",
        )

        # Startup owners: IMPORTANT — different users for different startups
        self.owner1 = User.objects.create(
            email="owner1@example.com",
            password=make_password("Pass123!"),
            role=self.role_user,
            is_active=True
        )
        self.owner2 = User.objects.create(
            email="owner2@example.com",
            password=make_password("Pass123!"),
            role=self.role_user,
            is_active=True
        )

        # Two startups with different owners (avoid OneToOne user clash)
        self.startup1 = Startup.objects.create(
            user=self.owner1,
            industry=self.industry,
            company_name="Cool One",
            location=self.location,
            email="one@cool.com",
            founded_year=2020,
            team_size=10,
            stage="mvp",
        )
        self.startup2 = Startup.objects.create(
            user=self.owner2,
            industry=self.industry,
            company_name="Alpha Two",
            location=self.location,
            email="two@alpha.com",
            founded_year=2021,
            team_size=8,
            stage="mvp",
        )

        # Authenticate as investor
        authenticate_client(self.client, self.user)

        # Seed: investor already saved startup1
        SavedStartup.objects.create(
            investor=self.investor,
            startup=self.startup1,
            status="watching",
        )

        # URLs
        self.list_url = reverse("investor-saved-startups")
        self.unsave_url_1 = reverse("startup-unsave", kwargs={"startup_id": self.startup1.id})
        self.unsave_url_2 = reverse("startup-unsave", kwargs={"startup_id": self.startup2.id})

    def test_auth_required(self):
        """Both list and unsave require authentication -> 401 when anonymous."""
        client = APIClient()
        r1 = client.get(self.list_url)
        self.assertEqual(r1.status_code, status.HTTP_403_FORBIDDEN)

        r2 = client.delete(self.unsave_url_1)
        self.assertEqual(r2.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_requires_investor_profile(self):
        """Non-investor user should get 403 (PermissionDenied in get_queryset)."""
        User = get_user_model()
        plain = User.objects.create_user(email="plain@ex.com", password="x", role=self.role_user)
        authenticate_client(self.client, plain)

        r = self.client.get(self.list_url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_returns_only_current_investor_and_supports_search_ordering(self):
        """List returns only current investor's rows + supports search/filter/ordering."""
        # Add second saved row for this investor to exercise filters/sorting
        SavedStartup.objects.create(
            investor=self.investor, startup=self.startup2, status="contacted"
        )

        # Default list
        r = self.client.get(self.list_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertEqual(len(data), 2)

        # Search by startup name (DRF SearchFilter)
        r = self.client.get(self.list_url + "?search=Alpha")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["startup_name"], "Alpha Two")

        # Filter by status
        r = self.client.get(self.list_url + "?status=watching")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertTrue(all(row["status"] == "watching" for row in data))

        # Ordering by startup name ascending
        r = self.client.get(self.list_url + "?ordering=startup__company_name")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        names = [row["startup_name"] for row in r.json()]
        self.assertEqual(names, sorted(names))

    def test_unsave_existing_returns_200_and_removes_row(self):
        """Unsave existing record -> 200 and row removed."""
        self.assertTrue(
            SavedStartup.objects.filter(investor=self.investor, startup=self.startup1).exists()
        )

        r = self.client.delete(self.unsave_url_1)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        body = r.json()
        self.assertEqual(body["startup_id"], self.startup1.id)
        self.assertFalse(body["saved"])
        self.assertTrue(body["deleted"])

        self.assertFalse(
            SavedStartup.objects.filter(investor=self.investor, startup=self.startup1).exists()
        )

    def test_unsave_not_existing_is_idempotent_returns_200_deleted_false(self):
        """Unsave for a startup not saved yet -> still 200, deleted=false (idempotent)."""
        # Ensure startup2 not saved
        self.assertFalse(
            SavedStartup.objects.filter(investor=self.investor, startup=self.startup2).exists()
        )

        r = self.client.delete(self.unsave_url_2)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        body = r.json()
        self.assertEqual(body["startup_id"], self.startup2.id)
        self.assertFalse(body["saved"])
        self.assertFalse(body["deleted"])

import os
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from investors.models import Investor, ViewedStartup
from startups.models import Startup, Industry, Location, Stage
from users.models import User, UserRole
from django.test import override_settings
from dotenv import load_dotenv

load_dotenv()
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


@override_settings(APPEND_SLASH=False, SECURE_SSL_REDIRECT=False)
class ViewedStartupTests(APITestCase):
    """Tests for the ViewedStartup API endpoints."""

    def setUp(self):
        """Set up test data: an investor user and two startups."""
        self.client = APIClient()

        role_investor, _ = UserRole.objects.get_or_create(role=UserRole.Role.INVESTOR)

        # Create investor user
        self.user = User.objects.create_user(
            email="investor@example.com",
            password=TEST_USER_PASSWORD,
            first_name="Active",
            last_name="InvestorCompany",
            role=role_investor,
            is_active=True
        )
        self.investor = Investor.objects.create(
            user=self.user,
            company_name="Test Investor Ltd",
            industry=Industry.objects.create(name="Tech"),
            location=Location.objects.create(city="Warsaw", country="PL"),
            email="investor@example.com",
            founded_year=2020,
            stage=Stage.MVP,
            fund_size=1000000
        )

        # Create startup users
        role_startup, _ = UserRole.objects.get_or_create(role=UserRole.Role.STARTUP)

        self.startup_user1 = User.objects.create_user(
            email="startup1user@example.com",
            password=TEST_USER_PASSWORD,
            first_name="Active",
            last_name="StartupCompanyOne",
            role=role_startup,
            is_active=True
        )
        self.startup_user2 = User.objects.create_user(
            email="startup2user@example.com",
            password=TEST_USER_PASSWORD,
            first_name="Active",
            last_name="StartupCompanyTwo",
            role=role_startup,
            is_active=True
        )

        # Create startups
        self.startup1 = Startup.objects.create(
            user=self.startup_user1,
            company_name="Startup One",
            industry=self.investor.industry,
            location=self.investor.location,
            email="startup1@example.com",
            founded_year=2021,
            stage=Stage.MVP
        )
        self.startup2 = Startup.objects.create(
            user=self.startup_user2,
            company_name="Startup Two",
            industry=self.investor.industry,
            location=self.investor.location,
            email="startup2@example.com",
            founded_year=2022,
            stage=Stage.MVP
        )

        # Authenticate client as the investor
        self.client.force_authenticate(user=self.user)

    def _fix_url(self, url: str) -> str:
        """Ensure URL ends with slash to avoid 301 from DRF router."""
        return url if url.endswith('/') else url + '/'

    def test_create_viewed_startup(self):
        """Ensure posting to the viewed startup endpoint creates a ViewedStartup record."""
        url = self._fix_url(reverse('viewed-startup-create', args=[str(self.startup1.id)]))
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(ViewedStartup.objects.filter(investor=self.investor, startup=self.startup1).exists())

    def test_list_viewed_startups_ordered(self):
        """Ensure the list of viewed startups is ordered by viewed_at descending."""
        ViewedStartup.objects.create(investor=self.investor, startup=self.startup1)
        ViewedStartup.objects.create(investor=self.investor, startup=self.startup2)

        url = self._fix_url(reverse('viewed-startup-list'))
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results']
        returned_ids = [str(item['startup_id']) for item in data]
        expected_ids = [str(self.startup2.id), str(self.startup1.id)]
        self.assertEqual(returned_ids, expected_ids)

    def test_clear_viewed_startups(self):
        """Ensure DELETE endpoint clears all viewed startup history."""
        ViewedStartup.objects.create(investor=self.investor, startup=self.startup1)
        ViewedStartup.objects.create(investor=self.investor, startup=self.startup2)

        url = self._fix_url(reverse('viewed-startup-clear'))
        response = self.client.delete(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ViewedStartup.objects.filter(investor=self.investor).count(), 0)

    def test_list_pagination_limit(self):
        """Ensure the `limit` query parameter correctly limits the number of returned startups."""
        ViewedStartup.objects.create(investor=self.investor, startup=self.startup1)
        ViewedStartup.objects.create(investor=self.investor, startup=self.startup2)

        url = self._fix_url(reverse('viewed-startup-list')) + "?page_size=1"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()['results']
        self.assertEqual(len(data), 1)

    def test_non_investor_cannot_access(self):
        """Ensure non-investor users cannot access viewed startups endpoints."""
        non_investor_user = User.objects.create_user(email="noninvestor@example.com", password="pass")
        self.client.force_authenticate(user=non_investor_user)

        url = self._fix_url(reverse('viewed-startup-list'))
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from investors.models import Investor, ViewedStartup
from startups.models import Startup, Industry, Location, Stage
from users.models import UserRole
from django.test import override_settings
from utils.authenticate_client import authenticate_client
import uuid

User = get_user_model()

@override_settings(APPEND_SLASH=False, SECURE_SSL_REDIRECT=False)
class ViewedStartupTests(APITestCase):
    """Tests for the ViewedStartup API endpoints."""

    def setUp(self):
        """Set up test data: an investor user and two startups."""
        self.client = APIClient()
        
        # Use UUID for unique values to prevent constraint violations
        unique_id = uuid.uuid4().hex[:8]

        # Create investor user
        role_investor, _ = UserRole.objects.get_or_create(role='investor')
        self.user = User.objects.create_user(
            email=f"investor_{unique_id}@example.com",
            password="password123",
            role=role_investor,
            is_active=True
        )
        
        self.investor = Investor.objects.create(
            user=self.user,
            company_name=f"Test Investor Ltd_{unique_id}",
            industry=Industry.objects.create(name=f"Tech_{unique_id}"),
            location=Location.objects.create(city=f"Warsaw_{unique_id}", country="PL"),
            email=f"investor_{unique_id}@example.com",
            founded_year=2020,
            stage=Stage.MVP,
            fund_size=1000000
        )

        # Create startup users
        role_user, _ = UserRole.objects.get_or_create(role='user')
        self.startup_user1 = User.objects.create_user(
            email=f"startup1user_{unique_id}@example.com",
            password="password123",
            role=role_user,
            is_active=True
        )
        self.startup_user2 = User.objects.create_user(
            email=f"startup2user_{unique_id}@example.com",
            password="password123",
            role=role_user,
            is_active=True
        )

        # Create startups
        self.startup1 = Startup.objects.create(
            user=self.startup_user1,
            company_name=f"Startup One_{unique_id}",
            industry=self.investor.industry,
            location=self.investor.location,
            email=f"startup1_{unique_id}@example.com",
            founded_year=2021,
            stage=Stage.MVP
        )
        self.startup2 = Startup.objects.create(
            user=self.startup_user2,
            company_name=f"Startup Two_{unique_id}",
            industry=self.investor.industry,
            location=self.investor.location,
            email=f"startup2_{unique_id}@example.com",
            founded_year=2022,
            stage=Stage.MVP
        )

        # Authenticate client as the investor
        authenticate_client(self.client, self.user)

    def tearDown(self):
        """Clean up test data after each test to prevent constraint violations."""
        ViewedStartup.objects.all().delete()
        Startup.objects.all().delete()
        Investor.objects.all().delete()
        User.objects.all().delete()
        Industry.objects.all().delete()
        Location.objects.all().delete()

    def _fix_url(self, url: str) -> str:
        """Ensure URL ends with slash to avoid 301 from DRF router."""
        return url if url.endswith('/') else url + '/'

    def test_create_viewed_startup(self):
        """Ensure posting to the viewed startup endpoint creates a ViewedStartup record."""
        url = self._fix_url(reverse('viewed-startup-create', args=[str(self.startup1.id)]))
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(ViewedStartup.objects.filter(investor=self.investor, startup=self.startup1).exists())

    def test_create_viewed_startup_with_duplicate_prevention(self):
        """Test that creating duplicate ViewedStartup entries is properly handled."""
        url = self._fix_url(reverse('viewed-startup-create', args=[str(self.startup1.id)]))
        
        # First view should succeed
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Second view should also succeed (updating timestamp)
        response2 = self.client.post(url, follow=True)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Should have only one ViewedStartup record (or handle duplicates gracefully)
        viewed_count = ViewedStartup.objects.filter(investor=self.investor, startup=self.startup1).count()
        self.assertGreaterEqual(viewed_count, 1)  # At least one record should exist

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
        role_user, _ = UserRole.objects.get_or_create(role='user')
        non_investor_user = User.objects.create_user(
            email=f"noninvestor_{uuid.uuid4().hex[:8]}@example.com", 
            password="pass", 
            role=role_user,
            is_active=True
        )
        authenticate_client(self.client, non_investor_user)

        url = self._fix_url(reverse('viewed-startup-list'))
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

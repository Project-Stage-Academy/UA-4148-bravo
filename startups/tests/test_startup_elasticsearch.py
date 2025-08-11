from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.db.models.signals import post_save
from startups.signals import update_startup_document
from users.models import User
from startups.models import Startup, Industry, Location


class StartupElasticsearchTests(TestCase):
    """Test Elasticsearch-based search and filters for startups."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Disable ES update signal to avoid real Elasticsearch calls in tests
        post_save.disconnect(update_startup_document, sender=Startup)

    @classmethod
    def tearDownClass(cls):
        # Re-enable signal after tests are done
        post_save.connect(update_startup_document, sender=Startup)
        super().tearDownClass()

    def setUp(self):
        """Set up test data including user, industries, locations, and startups."""
        self.client = APIClient()

        # Create and authenticate test user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        # Create some industries
        tech = Industry.objects.create(name="Technology")
        energy = Industry.objects.create(name="Energy")
        healthcare = Industry.objects.create(name="Healthcare")

        # Create locations with 2-letter ISO country codes
        usa = Location.objects.create(country="US")
        germany = Location.objects.create(country="DE")
        canada = Location.objects.create(country="CA")

        # Create startups with correct field names and types
        self.startup1 = Startup.objects.create(
            user=self.user,
            company_name="TechVision",
            description="Innovative AI solutions",
            location=usa,
            funding_stage="Seed",
            investment_needs=500000,  # Integer, not string
            company_size="Small",
            is_active=True,
            industry=tech,
        )

        self.startup2 = Startup.objects.create(
            user=self.user,
            company_name="GreenFuture",
            description="Eco-friendly energy startup",
            location=germany,
            funding_stage="Series A",
            investment_needs=750000,
            company_size="Medium",
            is_active=True,
            industry=energy,
        )

        self.startup3 = Startup.objects.create(
            user=self.user,
            company_name="MediCare Plus",
            description="Healthcare services for seniors",
            location=canada,
            funding_stage="Series B",
            investment_needs=1000000,
            company_size="Large",
            is_active=False,
            industry=healthcare,
        )

    def test_empty_query_returns_all_startups(self):
        url = reverse('startup-search')
        response = self.client.get(url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_search_by_description(self):
        url = reverse('startup-search')
        response = self.client.get(url, {'q': 'AI'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "TechVision")

    def test_filter_by_company_size(self):
        url = reverse('startup-search')
        response = self.client.get(url, {'company_size': 'Medium'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "GreenFuture")

    def test_filter_by_industry_and_active_status(self):
        url = reverse('startup-search')
        response = self.client.get(url, {'industry': 'Healthcare', 'is_active': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "MediCare Plus")

    def test_filter_by_location_country(self):
        url = reverse('startup-search')
        response = self.client.get(url, {'location_country': 'DE'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "GreenFuture")

    def test_no_results_for_non_existent_company_name(self):
        url = reverse('startup-search')
        response = self.client.get(url, {'q': 'NonExistent'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_ordering_by_company_name(self):
        url = reverse('startup-search')
        response = self.client.get(url, {'ordering': 'company_name'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [startup['company_name'] for startup in response.data]
        self.assertEqual(names, sorted(names))

    def test_search_by_investment_needs(self):
        url = reverse('startup-search')
        response = self.client.get(url, {'investment_needs': '500000'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "TechVision")

    def test_combined_filters_work_correctly(self):
        url = reverse('startup-search')
        response = self.client.get(url, {'industry': 'Technology', 'location_country': 'US', 'is_active': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "TechVision")

    def test_short_view_returns_minimal_data(self):
        url = reverse('startup-search')
        response = self.client.get(url, {'short': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if response.data:
            keys = list(response.data[0].keys())
            self.assertTrue(set(keys).issubset({'id', 'company_name'}))


# Standard library
from django.urls import reverse

# Third-party libraries
import pytest
from rest_framework.test import APIClient
from rest_framework import status

# Local application imports
from users.models import User
from startups.models import Startup, Industry, Location


@pytest.mark.django_db
class TestStartupElasticsearch:
    """Test Elasticsearch-based search and filters for startups."""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Create test user, industries, locations, and startups."""
        self.client = APIClient()

        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

        tech = Industry.objects.create(name="Technology")
        energy = Industry.objects.create(name="Energy")
        healthcare = Industry.objects.create(name="Healthcare")

        usa = Location.objects.create(country="US")
        germany = Location.objects.create(country="DE")
        canada = Location.objects.create(country="CA")

        self.startup1 = Startup.objects.create(
            user=self.user,
            company_name="TechVision",
            description="Innovative AI solutions",
            location=usa,
            funding_stage="Seed",
            investment_needs=500000,
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
        """Should return all startups when no filters are applied."""
        response = self.client.get(reverse('startup-search'), {})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_search_by_description(self):
        """Should return startups matching description query."""
        response = self.client.get(reverse('startup-search'), {'q': 'AI'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['company_name'] == "TechVision"

    @pytest.mark.parametrize("filter_key,filter_value,expected_name", [
        ('company_size', 'Medium', "GreenFuture"),
        ('industry', 'Healthcare', "MediCare Plus"),
        ('location_country', 'DE', "GreenFuture"),
    ])
    def test_filtering_by_various_fields(self, filter_key, filter_value, expected_name):
        """Should return correct startup for each filter."""
        response = self.client.get(reverse('startup-search'), {filter_key: filter_value})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['company_name'] == expected_name

    def test_filter_by_industry_and_active_status(self):
        """Should return inactive healthcare startup."""
        response = self.client.get(reverse('startup-search'), {'industry': 'Healthcare', 'is_active': 'false'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['company_name'] == "MediCare Plus"

    def test_no_results_for_non_existent_company_name(self):
        """Should return empty list for unknown search query."""
        response = self.client.get(reverse('startup-search'), {'q': 'NonExistent'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_invalid_filter_value_returns_empty(self):
        """Should return no results for invalid filter values."""
        response = self.client.get(reverse('startup-search'), {'company_size': 'Gigantic'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_ordering_by_company_name(self):
        """Should return startups ordered alphabetically by company name."""
        response = self.client.get(reverse('startup-search'), {'ordering': 'company_name'})
        assert response.status_code == status.HTTP_200_OK
        names = [startup['company_name'] for startup in response.data]
        assert names == sorted(names)

    def test_search_by_investment_needs(self):
        """Should return startup matching investment needs."""
        response = self.client.get(reverse('startup-search'), {'investment_needs': '500000'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['company_name'] == "TechVision"

    def test_combined_filters_work_correctly(self):
        """Should return startup matching multiple filters."""
        response = self.client.get(reverse('startup-search'), {
            'industry': 'Technology',
            'location_country': 'US',
            'is_active': 'true'
        })
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['company_name'] == "TechVision"

    def test_short_view_returns_minimal_data(self):
        """Should return only 'id' and 'company_name' in short view."""
        response = self.client.get(reverse('startup-search'), {'short': 'true'})
        assert response.status_code == status.HTTP_200_OK
        if response.data:
            keys = set(response.data[0].keys())
            assert keys.issubset({'id', 'company_name'})

    def test_unauthenticated_access_denied(self):
        """Should return 401 for unauthenticated user."""
        client = APIClient()
        response = client.get(reverse('startup-search'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unknown_query_param_does_not_break(self):
        """Should ignore unknown query params and return all startups."""
        response = self.client.get(reverse('startup-search'), {'unknown': 'value'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_response_contains_expected_keys(self):
        """Should include expected fields in response."""
        response = self.client.get(reverse('startup-search'))
        assert response.status_code == status.HTTP_200_OK
        assertIn('company_name', response.data[0])
        assertNotIn('non_existent_field', response.data[0])

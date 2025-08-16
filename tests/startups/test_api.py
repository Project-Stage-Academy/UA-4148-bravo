from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase

from startups.models import Startup
from tests.startups.test_disable_signal_mixin import DisableElasticsearchSignalsMixin
from tests.test_base_case import BaseAPITestCase


class StartupAPITests(DisableElasticsearchSignalsMixin, BaseAPITestCase, TestCase):
    """API tests for Startup endpoints (CRUD, filtering, search)."""

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        # Force authenticate user for all requests
        self.client.force_authenticate(user=self.user)

        # Basic startup payload
        self.startup_data = {
            'company_name': 'Great',
            'team_size': 25,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'email': 'great@example.com',
        }

        # Base URL for StartupViewSet
        self.url = reverse('startups-list')

    def test_create_startup_success(self):
        """Test successful creation of a startup."""
        response = self.client.post(self.url, self.startup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        startup = Startup.objects.get(pk=response.data['id'])
        self.assertEqual(startup.user, self.user)

    def test_get_startup_list(self):
        """Test retrieving list of startups."""
        self.get_or_create_startup(
            user=self.user,
            company_name='ListStartup',
            industry=self.industry,
            location=self.location
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_startup_validation_error(self):
        """Test creating a startup with invalid data."""
        data = self.startup_data.copy()
        data['company_name'] = ''
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_name', response.data)

    def test_filter_by_industry(self):
        """Test filtering startups by industry."""
        startup_in = self.get_or_create_startup(
            user=self.user,
            industry=self.industry,
            location=self.location,
            company_name='IndustryA'
        )
        other_industry = self.get_or_create_industry(name='Machinery Building')
        other_user = self.get_or_create_user("greatemployee@example.com", "Great", "Employee")
        self.get_or_create_startup(
            user=other_user,
            industry=other_industry,
            location=self.location,
            company_name='IndustryB'
        )
        response = self.client.get(self.url, {'industry': self.industry.pk})
        # Ensure we access response.data safely (it might be list of dicts)
        names = [s.get('company_name') for s in response.data if isinstance(s, dict)]
        self.assertIn(startup_in.company_name, names)

    def test_search_by_company_name(self):
        """Test searching startups by company_name."""
        self.get_or_create_startup(
            user=self.user,
            company_name='Searchable Startup',
            industry=self.industry,
            location=self.location
        )
        response = self.client.get(self.url, {'search': 'Searchable'})
        # Safely handle response data
        self.assertTrue(any('Searchable' in s.get('company_name', '') for s in response.data if isinstance(s, dict)))

    def test_delete_startup(self):
        """Test deletion of a startup via ViewSet (DELETE)."""
        startup = self.get_or_create_startup(
            user=self.user,
            company_name='ToDelete',
            industry=self.industry,
            location=self.location
        )
        # Use the ViewSet URL, not the detail-only view
        url_detail = reverse('startups-detail', args=[startup.pk])
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Startup.objects.filter(pk=startup.pk).exists())



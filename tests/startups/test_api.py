from django.urls import reverse
from rest_framework import status
from startups.models import Startup
from tests.test_base_case import BaseAPITestCase
from unittest.mock import patch
from rest_framework.test import APIClient
from django.core.exceptions import ValidationError as DjangoValidationError

from tests.test_disable_signal_mixin import DisableSignalMixin


class StartupAPITests(DisableSignalMixin, BaseAPITestCase):
    """Test suite for Startup API endpoints, including creation and retrieval of startups."""

    def setUp(self):
        super().setUp()
        self.startup_data = {
            'company_name': 'Great',
            'team_size': 25,
            'user': self.user.pk,  # Request.user is always used
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'email': 'great@example.com',
        }
        self.url = reverse('startup-list')

    def test_create_startup_success(self):
        """Test successful creation of a startup via POST request."""
        response = self.client.post(self.url, self.startup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.data
        self.assertEqual(data['company_name'], 'Great')
        self.assertEqual(data['team_size'], 25)
        self.assertEqual(data['founded_year'], 2020)
        self.assertEqual(data['email'], 'great@example.com')
        startup = Startup.objects.get(pk=data['id'])
        self.assertEqual(startup.user, self.user)

    def test_get_startup_list(self):
        """GET request returns list of startups including at least one from setup."""
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
        """Creating a startup with empty company_name returns 400."""
        data = self.startup_data.copy()
        data['company_name'] = ''
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_name', response.data)

    def test_filter_by_industry(self):
        """Filter startups by industry returns only relevant startups."""
        startup1 = self.get_or_create_startup(
            user=self.user, industry=self.industry, location=self.location,
            company_name='IndustryA'
        )
        other_industry = self.get_or_create_industry(name='Machinery Building')
        other_user = self.get_or_create_user("greatemployee@example.com", "Great", "Employee")
        startup2 = self.get_or_create_startup(
            user=other_user,
            industry=other_industry,
            location=self.location,
            company_name='IndustryB'
        )
        response = self.client.get(self.url, {'industry': self.industry.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_names = [s['company_name'] for s in response.data]
        self.assertIn(startup1.company_name, returned_names)
        self.assertNotIn(startup2.company_name, returned_names)

    def test_search_by_company_name(self):
        """Searching by partial company name returns correct startups."""
        self.get_or_create_startup(
            user=self.user, company_name='Searchable Startup',
            industry=self.industry, location=self.location
        )
        response = self.client.get(self.url, {'search': 'Searchable'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any('Searchable' in s['company_name'] for s in response.data))

    def test_retrieve_startup_detail(self):
        """Retrieving a single startup returns correct details."""
        startup = self.get_or_create_startup(
            user=self.user, company_name='DetailStartup',
            industry=self.industry, location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'DetailStartup')

    def test_update_startup_success(self):
        """Full update of a startup works and returns updated data."""
        startup = self.get_or_create_startup(
            user=self.user, company_name='OldName',
            industry=self.industry, location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        data = {
            'company_name': 'UpdatedName',
            'team_size': 20,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2018,
            'email': 'updated@example.com'
        }
        response = self.client.put(url_detail, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'UpdatedName')

    def test_partial_update_startup(self):
        """Partial update works correctly."""
        startup = self.get_or_create_startup(
            user=self.user, company_name='PartialUpdate',
            industry=self.industry, location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        data = {'company_name': 'PartialUpdatedName'}
        response = self.client.patch(url_detail, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'PartialUpdatedName')

    def test_update_startup_validation_error(self):
        """Updating startup with invalid data returns 400."""
        startup = self.get_or_create_startup(
            user=self.user, company_name='ValidName',
            industry=self.industry, location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        data = {'company_name': ''}
        response = self.client.patch(url_detail, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_name', response.data)

    def test_delete_startup(self):
        """Deleting a startup removes it and returns 204."""
        startup = self.get_or_create_startup(
            user=self.user, company_name='ToDelete',
            industry=self.industry, location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Startup.objects.filter(pk=startup.pk).exists())

    def test_create_startup_user_is_ignored(self):
        """Passed user is ignored; request.user is used."""
        other_user = self.get_or_create_user("fake@example.com", "Fake", "User")
        data = self.startup_data.copy()
        data['user'] = other_user.pk
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        startup = Startup.objects.get(pk=response.data['id'])
        self.assertEqual(startup.user, self.user)

    @patch('startups.models.Startup.clean', side_effect=Exception("Invalid data"))
    def test_create_startup_model_clean_error(self, mock_clean):
        """Simulate model validation error during creation, should return 400."""
        mock_clean.side_effect = DjangoValidationError({'non_field_errors': ['Invalid data']})
        response = self.client.post(self.url, self.startup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'][0], 'Invalid data')

    def test_get_list_unauthenticated(self):
        """Unauthenticated GET returns 401."""
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_startup_returns_updated_fields(self):
        """After update, all updated fields are returned correctly."""
        startup = self.get_or_create_startup(
            user=self.user,
            company_name='InitialName',
            industry=self.industry,
            location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        data = {
            'company_name': 'NewName',
            'team_size': 30,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2021,
            'email': 'new@example.com'
        }
        response = self.client.put(url_detail, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'NewName')
        self.assertEqual(response.data['team_size'], 30)
        self.assertEqual(response.data['founded_year'], 2021)
        self.assertEqual(response.data['email'], 'new@example.com')






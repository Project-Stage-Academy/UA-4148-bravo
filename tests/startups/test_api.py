from unittest.mock import patch
import unittest

from django.urls import reverse, NoReverseMatch
from rest_framework import status
from startups.models import Startup
from tests.test_base_case import BaseAPITestCase
from rest_framework.test import APIClient
from django.core.exceptions import ValidationError as DjangoValidationError


class StartupAPITests(BaseAPITestCase):
    """
    API tests for Startup endpoints (CRUD, filtering, search).
    ES indexing is mocked to avoid external calls during tests.
    """

    def setUp(self):
        super().setUp()
        # Patch ES registry to avoid indexing on save/delete during tests
        self.es_update_patcher = patch('django_elasticsearch_dsl.registries.registry.update')
        self.es_delete_patcher = patch('django_elasticsearch_dsl.registries.registry.delete')
        self.mock_es_update = self.es_update_patcher.start()
        self.mock_es_delete = self.es_delete_patcher.start()
        self.addCleanup(self.es_update_patcher.stop)
        self.addCleanup(self.es_delete_patcher.stop)

        self.startup_data = {
            'company_name': 'Great',
            'team_size': 25,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'email': 'great@example.com',
        }
        self.url = reverse('startup-list')

    # --- Create / Read ---

    def test_create_startup_success(self):
        """
        POST /startup/ should create a startup and return 201 with payload.
        """
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
        """
        GET /startup/ should return a list of startups (>= 1).
        """
        self.get_or_create_startup(
            user=self.user,
            company_name='ListStartup',
            industry=self.industry,
            location=self.location
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    # --- Validations ---

    def test_create_startup_validation_error(self):
        """
        Empty company_name should return 400 and validation error message.
        """
        data = self.startup_data.copy()
        data['company_name'] = ''
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_name', response.data)

    # --- Filtering / Search ---

    def test_filter_by_industry(self):
        """
        Filtering by industry should include only startups in that industry.
        """
        startup_in = self.get_or_create_startup(
            user=self.user, industry=self.industry, location=self.location,
            company_name='IndustryA'
        )
        other_industry = self.get_or_create_industry(name='Machinery Building')
        other_user = self.get_or_create_user("greatemployee@example.com", "Great", "Employee")
        startup_out = self.get_or_create_startup(
            user=other_user,
            industry=other_industry,
            location=self.location,
            company_name='IndustryB'
        )
        response = self.client.get(self.url, {'industry': self.industry.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [s['company_name'] for s in response.data]
        self.assertIn(startup_in.company_name, names)
        self.assertNotIn(startup_out.company_name, names)

    def test_search_by_company_name(self):
        """
        Searching by partial company_name should return matching startups.
        """
        self.get_or_create_startup(
            user=self.user, company_name='Searchable Startup',
            industry=self.industry, location=self.location
        )
        response = self.client.get(self.url, {'search': 'Searchable'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any('Searchable' in s['company_name'] for s in response.data))

    # --- Detail / Update / Delete ---

    def test_retrieve_startup_detail(self):
        """
        GET /startup/{id}/ should return startup details.
        """
        startup = self.get_or_create_startup(
            user=self.user, company_name='DetailStartup',
            industry=self.industry, location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'DetailStartup')

    def test_update_startup_success(self):
        """
        PUT /startup/{id}/ should update startup and return 200 with payload.
        """
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
        """
        PATCH /startup/{id}/ should update only provided fields.
        """
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
        """
        Empty company_name on update should return 400 with error.
        """
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
        """
        DELETE /startup/{id}/ should remove startup and return 204.
        """
        startup = self.get_or_create_startup(
            user=self.user, company_name='ToDelete',
            industry=self.industry, location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Startup.objects.filter(pk=startup.pk).exists())

    # --- Auth / Model validation integration ---

    def test_create_startup_user_is_ignored(self):
        """
        Even if another user id is provided, the API should set request.user.
        """
        other_user = self.get_or_create_user("fake@example.com", "Fake", "User")
        data = self.startup_data.copy()
        data['user'] = other_user.pk
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        startup = Startup.objects.get(pk=response.data['id'])
        self.assertEqual(startup.user, self.user)

    @patch('startups.models.Startup.clean', side_effect=Exception("Invalid data"))
    def test_create_startup_model_clean_error(self, mock_clean):
        """
        Simulate model validation error from Startup.clean() → API returns 400.
        """
        from django.core.exceptions import ValidationError as DJV
        mock_clean.side_effect = DJV({'non_field_errors': ['Invalid data']})
        response = self.client.post(self.url, self.startup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'][0], 'Invalid data')

    def test_get_list_unauthenticated(self):
        """
        Unauthenticated request to /startup/ should return 401.
        """
        client = APIClient()
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_startup_returns_updated_fields(self):
        """
        After PUT, response should contain updated values.
        """
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


# -------- Optional block for "startup-search" route (safe to remove/keep) --------

try:
    reverse('startup-search')
    _HAS_STARTUP_SEARCH = True
except NoReverseMatch:
    _HAS_STARTUP_SEARCH = False


@unittest.skipUnless(_HAS_STARTUP_SEARCH, "startup-search route is not configured")
class StartupSearchRouteTests(BaseAPITestCase):
    """
    Lightweight tests for the optional /startup-search/ endpoint.
    Skipped automatically if route is not present.
    """

    def setUp(self):
        super().setUp()
        # Avoid ES indexing calls if search view triggers them on create
        self.es_update_patcher = patch('django_elasticsearch_dsl.registries.registry.update')
        self.es_delete_patcher = patch('django_elasticsearch_dsl.registries.registry.delete')
        self.es_update_patcher.start()
        self.es_delete_patcher.start()
        self.addCleanup(self.es_update_patcher.stop)
        self.addCleanup(self.es_delete_patcher.stop)

        # Seed a few startups
        self.s1 = self.get_or_create_startup(
            user=self.user, company_name="TechVision",
            description="Innovative AI solutions",
            industry=self.industry, location=self.location
        )
        other_industry = self.get_or_create_industry("Energy")
        self.s2 = self.get_or_create_startup(
            user=self.user, company_name="GreenFuture",
            description="Eco-friendly energy startup",
            industry=other_industry, location=self.location
        )

        self.url = reverse('startup-search')

    def test_empty_query_returns_all(self):
        resp = self.client.get(self.url, {})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 2)

    def test_search_by_company_name(self):
        resp = self.client.get(self.url, {'q': 'Tech'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [r.get('company_name') for r in resp.data]
        self.assertIn("TechVision", names)

    def test_ordering_by_company_name(self):
        resp = self.client.get(self.url, {'ordering': 'company_name'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [r.get('company_name') for r in resp.data]
        self.assertEqual(names, sorted(names))

    def test_unknown_query_param_is_ignored(self):
        resp = self.client.get(self.url, {'unknown': 'value'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_access_denied(self):
        client = APIClient()
        resp = client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


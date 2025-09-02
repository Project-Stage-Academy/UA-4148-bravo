from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from startups.models import Startup
from tests.test_base_case import BaseAPITestCase
from unittest.mock import patch
from rest_framework.test import APIClient
from django.core.exceptions import ValidationError as DjangoValidationError
from utils.authenticate_client import authenticate_client


@override_settings(SECURE_SSL_REDIRECT=False)
class StartupAPITests(BaseAPITestCase):
    """
    Test suite for Startup API endpoints, including creation and retrieval of startups.
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()
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

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_create_startup_success(self, mock_has_object_permission, mock_has_permission):
        """
        Test that a startup can be successfully created via POST request to the startup-list endpoint.
        Verifies that the response status is HTTP 201 Created and the returned data matches the input.
        """
        authenticate_client(self.client, self.user)
        response = self.client.post(self.url, self.startup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.data
        self.assertEqual(data['company_name'], 'Great')
        self.assertEqual(data['team_size'], 25)
        self.assertEqual(data['founded_year'], 2020)
        self.assertEqual(data['email'], 'great@example.com')

        startup = Startup.objects.get(pk=data['id'])
        self.assertEqual(startup.user, self.user)

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_get_startup_list(self, mock_has_object_permission, mock_has_permission):
        """
        Test that the GET request to startup-list endpoint returns a list of startups,
        including at least one startup created in the test setup.
        Verifies response status is HTTP 200 OK and that at least one startup is returned.
        """
        authenticate_client(self.client, self.user)
        self.get_or_create_startup(
            user=self.user,
            company_name='ListStartup',
            industry=self.industry,
            location=self.location
        )
        url = reverse('startup-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_create_startup_validation_error(self, mock_has_object_permission, mock_has_permission):
        """
        Ensure that creating a startup with invalid data (empty company_name)
        returns HTTP 400 Bad Request and includes the relevant validation error.
        """
        authenticate_client(self.client, self.user)
        data = self.startup_data.copy()
        data['company_name'] = ''
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_name', response.data)

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_filter_by_industry(self, mock_has_object_permission, mock_has_permission):
        """
        Verify that the industry filter correctly returns startups only
        within the specified industry and excludes others.
        """
        authenticate_client(self.client, self.user)
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

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_search_by_company_name(self, mock_has_object_permission, mock_has_permission):
        """
        Ensure that searching by a partial company name returns the matching startups.
        """
        authenticate_client(self.client, self.user)
        self.get_or_create_startup(
            user=self.user, company_name='Searchable Startup',
            industry=self.industry, location=self.location
        )
        response = self.client.get(self.url, {'search': 'Searchable'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any('Searchable' in s['company_name'] for s in response.data))

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_retrieve_startup_detail(self, mock_has_object_permission, mock_has_permission):
        """
        Verify that retrieving a single startup by its ID returns
        the correct details and HTTP 200 OK.
        """
        authenticate_client(self.client, self.user)
        startup = self.get_or_create_startup(
            user=self.user, company_name='DetailStartup',
            industry=self.industry, location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'DetailStartup')

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_update_startup_success(self, mock_has_object_permission, mock_has_permission):
        """
        Ensure that a full update (PUT) to a startup works and
        returns HTTP 200 OK with the updated data.
        """
        authenticate_client(self.client, self.user)
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

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_partial_update_startup(self, mock_has_object_permission, mock_has_permission):
        """
        Ensure that a partial update (PATCH) to a startup works and
        returns HTTP 200 OK with the updated field.
        """
        authenticate_client(self.client, self.user)
        startup = self.get_or_create_startup(
            user=self.user, company_name='PartialUpdate',
            industry=self.industry, location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        data = {'company_name': 'PartialUpdatedName'}
        response = self.client.patch(url_detail, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'PartialUpdatedName')

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_update_startup_validation_error(self, mock_has_object_permission, mock_has_permission):
        """
        Verify that updating a startup with invalid data
        (empty company_name) returns HTTP 400 Bad Request with errors.
        """
        authenticate_client(self.client, self.user)
        startup = self.get_or_create_startup(
            user=self.user, company_name='ValidName',
            industry=self.industry, location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        data = {'company_name': ''}
        response = self.client.patch(url_detail, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_name', response.data)

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_delete_startup(self, mock_has_object_permission, mock_has_permission):
        """
        Ensure that deleting a startup works, returns HTTP 204 No Content,
        and removes the object from the database.
        """
        authenticate_client(self.client, self.user)
        startup = self.get_or_create_startup(
            user=self.user, company_name='ToDelete',
            industry=self.industry, location=self.location
        )
        url_detail = reverse('startup-detail', args=[startup.pk])
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Startup.objects.filter(pk=startup.pk).exists())

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_create_startup_user_is_ignored(self, mock_has_object_permission, mock_has_permission):
        """
        Even if a different user ID is passed in request,
        Startup should be created with request.user.
        """
        authenticate_client(self.client, self.user)
        other_user = self.get_or_create_user("fake@example.com", "Fake", "User")
        data = self.startup_data.copy()
        data['user'] = other_user.pk
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        startup = Startup.objects.get(pk=response.data['id'])
        self.assertEqual(startup.user, self.user)

    @patch('startups.models.Startup.clean', side_effect=DjangoValidationError({'non_field_errors': ['Invalid data']}))
    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_create_startup_model_clean_error(self, mock_has_object_permission, mock_has_permission, mock_clean):
        """
        Simulate model validation error during creation.
        Should return HTTP 400.
        """
        authenticate_client(self.client, self.user)
        response = self.client.post(self.url, self.startup_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        self.assertEqual(response.data['non_field_errors'][0], 'Invalid data')

    def test_get_list_unauthenticated(self):
        """
        Unauthenticated request should return HTTP 401.
        """
        self.client.cookies.clear()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_update_startup_returns_updated_fields(self, mock_has_object_permission, mock_has_permission):
        """
        After update, API should return all updated fields correctly.
        """
        authenticate_client(self.client, self.user)
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

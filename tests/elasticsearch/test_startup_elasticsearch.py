from django.urls import reverse
from elasticsearch_dsl import Index
from rest_framework import status
from common.enums import Stage
from startups.documents import StartupDocument
from tests.elasticsearch.setup_tests_data import BaseElasticsearchAPITestCase
from unittest.mock import patch
from django.test.utils import override_settings


@override_settings(SECURE_SSL_REDIRECT=False)
class StartupElasticsearchTests(BaseElasticsearchAPITestCase):
    """
    Integration tests for the Startup API with an Elasticsearch backend.

    These tests verify that:
    - The Elasticsearch index is correctly created and queried.
    - The search API returns expected results for various queries and filters.
    - Data setup is performed using factory_boy factories for cleaner test code.
    """

    def setUp(self):
        """ Create the Elasticsearch index and allow ES to index the documents. """
        super().setUp()
        self.index = Index('startups')
        try:
            self.index.delete()
        except:
            pass
        self.index.create()
        StartupDocument._doc_type.mapping.save('startups')

    def tearDown(self):
        """
        Delete the Elasticsearch index after each test.
        """
        try:
            self.index.delete()
        except Exception:
            pass

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_empty_query_returns_all_startups(self, mock_has_object_permission, mock_has_permission):
        """
        Ensure that an empty search query returns all startups in the index.
        """
        url = reverse('startup-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_no_results_for_non_existent_company_name(self, mock_has_object_permission, mock_has_permission):
        """
        Ensure that searching for a non-existent company name returns no results.
        """
        url = reverse('startup-list')
        response = self.client.get(url, {'search': 'Nonexistent Company'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    @patch("users.permissions.IsStartupUser.has_permission", return_value=True)
    @patch("users.permissions.IsStartupUser.has_object_permission", return_value=True)
    def test_combined_filters_work_correctly(self, mock_has_object_permission, mock_has_permission):
        """
        Ensure that filtering by stage and location returns the correct startup.
        """
        url = reverse('startup-list')
        response = self.client.get(url, {
            'stage': Stage.MVP,
            'location.country': 'DE'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "ShopFast")

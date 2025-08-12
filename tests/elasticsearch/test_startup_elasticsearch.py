import time
from django.conf import settings
from django.urls import reverse
from elasticsearch_dsl import Index
from elasticsearch_dsl.connections import connections
from rest_framework import status
from common.enums import Stage
from startups.documents import StartupDocument
from tests.test_base import DisableSignalMixinStartup, BaseAPITestCase


class StartupElasticsearchTests(DisableSignalMixinStartup, BaseAPITestCase):
    """
    Integration tests for the Startup API with an Elasticsearch backend.

    These tests verify that:
    - The Elasticsearch index is correctly created and queried.
    - The search API returns expected results for various queries and filters.
    - Data setup is performed using factory_boy factories for cleaner test code.
    """

    @classmethod
    def setUpClass(cls):
        """
        Configure Elasticsearch connection before any tests run.
        """
        super().setUpClass()
        es_config = getattr(settings, 'ELASTICSEARCH_DSL', {}).get('default', {})
        hosts = es_config.get('hosts', 'http://localhost:9200')
        connections.configure(default={'hosts': hosts})

    def setUp(self):
        """
        Create the Elasticsearch index, set up test data using factories,
        and allow ES to index the documents.
        """
        self.index = Index('startups')
        try:
            self.index.delete()
        except Exception:
            pass
        self.index.create()
        StartupDocument._doc_type.mapping.save('startups')

        self.user1 = UserFactory()
        self.user2 = UserFactory()

        self.industry1 = IndustryFactory(name="Fintech")
        self.industry2 = IndustryFactory(name="E-commerce")

        self.location1 = LocationFactory(country="US")
        self.location2 = LocationFactory(country="DE")

        self.startup1 = StartupFactory(
            user=self.user1,
            industry=self.industry1,
            company_name="Fintech Solutions",
            description="Leading fintech platform",
            location=self.location1,
            email="ideastartup@example.com",
            founded_year=2020,
            team_size=10,
            stage=Stage.IDEA,
        )

        self.startup2 = StartupFactory(
            user=self.user2,
            industry=self.industry2,
            company_name="ShopFast",
            description="E-commerce made simple",
            location=self.location2,
            email="mvpstartup@example.com",
            founded_year=2020,
            team_size=15,
            stage=Stage.MVP,
        )

        time.sleep(1)

    def tearDown(self):
        """
        Delete the Elasticsearch index after each test.
        """
        try:
            self.index.delete()
        except Exception:
            pass

    def test_empty_query_returns_all_startups(self):
        """
        Ensure that an empty search query returns all startups in the index.
        """
        url = reverse('startup-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_no_results_for_non_existent_company_name(self):
        """
        Ensure that searching for a non-existent company name returns no results.
        """
        url = reverse('startup-list')
        response = self.client.get(url, {'search': 'Nonexistent Company'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_combined_filters_work_correctly(self):
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

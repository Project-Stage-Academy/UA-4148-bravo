from rest_framework.test import APITestCase
from rest_framework import status
from startups.models import Startup, Industry, Location
from startups.documents import StartupDocument
from django.urls import reverse
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import Index
from django.conf import settings
import time

class StartupElasticsearchTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Configure Elasticsearch connection for tests
        es_config = getattr(settings, 'ELASTICSEARCH_DSL', {}).get('default', {})
        hosts = es_config.get('hosts', 'localhost:9200')
        connections.configure(default={'hosts': hosts})

    def setUp(self):
        self.client = self.client
        self.index = Index('startups_test')
        # Try to delete the index if it exists, ignore errors
        try:
            self.index.delete()
        except:
            pass
        self.index.create()
        # Apply the document mapping to the index
        StartupDocument._doc_type.mapping.save('startups_test')

        self.industry1 = Industry.objects.create(name="Fintech")
        self.industry2 = Industry.objects.create(name="E-commerce")
        self.location1 = Location.objects.create(country="USA")
        self.location2 = Location.objects.create(country="Germany")

        self.startup1 = Startup.objects.create(
            company_name="Fintech Solutions",
            description="Leading fintech platform.",
            funding_stage="Seed",
            location=self.location1
        )
        self.startup1.industries.add(self.industry1)

        self.startup2 = Startup.objects.create(
            company_name="ShopFast",
            description="E-commerce made simple.",
            funding_stage="Series A",
            location=self.location2
        )
        self.startup2.industries.add(self.industry2)
        
        time.sleep(1)

    def tearDown(self):
        try:
            self.index.delete()
        except:
            pass

    def test_empty_query_returns_all_startups(self):
        url = reverse('startup-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_no_results_for_non_existent_company_name(self):
        url = reverse('startup-list')
        response = self.client.get(url, {'search': 'Nonexistent Company'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_combined_filters_work_correctly(self):
        url = reverse('startup-list')
        response = self.client.get(url, {
            'funding_stage': 'Series A', 
            'location.country': 'Germany'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "ShopFast")
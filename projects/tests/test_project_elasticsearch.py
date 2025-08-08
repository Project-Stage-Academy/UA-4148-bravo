from rest_framework.test import APITestCase
from rest_framework import status
from projects.models import Project, Category
from startups.models import Startup
from django.urls import reverse
from elasticsearch_dsl.connections import connections
from elasticsearch.exceptions import ConnectionError
import time

class ProjectElasticsearchTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category1 = Category.objects.create(name="Tech")
        cls.category2 = Category.objects.create(name="Finance")
        cls.startup1 = Startup.objects.create(company_name="InnovateCo")
        cls.startup2 = Startup.objects.create(company_name="FinGrowth Inc.")

        cls.project1 = Project.objects.create(
            title="Search Engine for Startups",
            description="A powerful search tool.",
            category=cls.category1,
            startup=cls.startup1,
            goals="Improve discovery."
        )
        cls.project2 = Project.objects.create(
            title="Financial Dashboard",
            description="Real-time financial data.",
            category=cls.category2,
            startup=cls.startup2,
            goals="Provide analytics."
        )

    def setUp(self):
        self.client = self.client
        try:
            connections.get_connection().cluster.health()
            self.elasticsearch_available = True
        except ConnectionError:
            self.elasticsearch_available = False

        if self.elasticsearch_available:
            # Reindex manually if needed
            from projects.documents import ProjectDocument
            for project in Project.objects.all():
                ProjectDocument().update(project)

            time.sleep(1)

    def test_empty_query_returns_all_projects(self):
        if not self.elasticsearch_available:
            self.skipTest("Elasticsearch is not available")
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_no_results_for_non_existent_title(self):
        if not self.elasticsearch_available:
            self.skipTest("Elasticsearch is not available")
        url = reverse('project-list')
        response = self.client.get(url, {'search': 'nonexistent_project'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_combined_filters_work_correctly(self):
        if not self.elasticsearch_available:
            self.skipTest("Elasticsearch is not available")
        url = reverse('project-list')
        response = self.client.get(url, {
            'category.name': 'Tech',
            'startup.company_name': 'InnovateCo'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Search Engine for Startups")

    def test_invalid_filter_field_returns_bad_request(self):
        if not self.elasticsearch_available:
            self.skipTest("Elasticsearch is not available")
        url = reverse('project-list')
        response = self.client.get(url, {'nonexistent_field': 'value'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

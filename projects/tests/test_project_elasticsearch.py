import os
import time  # Standard library

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status  # Third-party libraries

from elasticsearch_dsl.connections import connections
from elasticsearch.exceptions import ConnectionError  # Third-party libraries

from projects.models import Project, Category
from startups.models import Startup  # Local application imports


def reindex_projects():
    from projects.documents import ProjectDocument
    for project in Project.objects.all():
        ProjectDocument().update(project)


def wait_for_index(index_name, timeout=5):
    es = connections.get_connection()
    for _ in range(timeout):
        if es.indices.exists(index=index_name):
            return
        time.sleep(1)
    raise RuntimeError(f"Index '{index_name}' not ready after {timeout} seconds")


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
        if os.environ.get("SKIP_ELASTICSEARCH_TESTS") == "1":
            self.skipTest("Elasticsearch tests are disabled via environment variable")

        try:
            connections.get_connection().cluster.health()
        except ConnectionError:
            self.skipTest("Elasticsearch is not available")

        reindex_projects()
        wait_for_index(index_name="projects")

    def test_empty_query_returns_all_projects(self):
        # Arrange
        url = reverse('project-list')

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_no_results_for_non_existent_title(self):
        # Arrange
        url = reverse('project-list')
        params = {'search': 'nonexistent_project'}

        # Act
        response = self.client.get(url, params)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_combined_filters_work_correctly(self):
        # Arrange
        url = reverse('project-list')
        params = {
            'category.name': 'Tech',
            'startup.company_name': 'InnovateCo'
        }

        # Act
        response = self.client.get(url, params)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Search Engine for Startups")

    def test_invalid_filter_field_returns_bad_request(self):
        # Arrange
        url = reverse('project-list')
        params = {'nonexistent_field': 'value'}

        # Act
        response = self.client.get(url, params)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_combined_filters_work_correctly(self):
        url = reverse('project-list')
        response = self.client.get(url, {
            'category.name': 'Tech',
            'startup.company_name': 'InnovateCo'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Search Engine for Startups")

    def test_invalid_filter_field_returns_bad_request(self):
        url = reverse('project-list')
        response = self.client.get(url, {'nonexistent_field': 'value'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


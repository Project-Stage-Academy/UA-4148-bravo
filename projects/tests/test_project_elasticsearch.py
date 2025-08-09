import time

from django.conf import settings
from django.urls import reverse
from elasticsearch import Elasticsearch
from elasticsearch_dsl.connections import connections
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from projects.documents import ProjectDocument
from projects.models import Project, Category
from startups.models import Startup
from users.models import UserRole, User


def wait_for_elasticsearch(host='http://localhost:9200', timeout=30):
    client = Elasticsearch(host)
    start_time = time.time()
    while True:
        try:
            if client.ping():
                break
        except Exception:
            pass
        if time.time() - start_time > timeout:
            raise RuntimeError("Elasticsearch server is not available")
        time.sleep(1)


class ProjectElasticsearchTests(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        wait_for_elasticsearch()
        ProjectDocument.init()
        # Configure Elasticsearch connection for tests
        es_config = getattr(settings, 'ELASTICSEARCH_DSL', {}).get('default', {})
        hosts = es_config.get('hosts', 'http://localhost:9200')
        connections.configure(default={'hosts': hosts})

    def setUp(self):
        role = UserRole.objects.get(role=UserRole.Role.USER)
        self.user = User.objects.create_user(
            email='apistartup@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Startup',
            role=role,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        wait_for_elasticsearch()
        client = connections.get_connection()
        try:
            client.indices.delete(index=ProjectDocument._index._name, ignore=[400, 404])
        except Exception:
            pass
        ProjectDocument.init()

        self.category1 = Category.objects.create(name="Tech")
        self.category2 = Category.objects.create(name="Finance")
        self.startup1 = Startup.objects.create(company_name="InnovateCo")
        self.startup2 = Startup.objects.create(company_name="FinGrowth Inc.")

        self.project1 = Project.objects.create(
            title="Search Engine for Startups",
            description="A powerful search tool.",
            category=self.category1,
            startup=self.startup1,
            goals="Improve discovery."
        )
        self.project2 = Project.objects.create(
            title="Financial Dashboard",
            description="Real-time financial data.",
            category=self.category2,
            startup=self.startup2,
            goals="Provide analytics."
        )
        for project in Project.objects.all():
            ProjectDocument().update(project)
        time.sleep(1)

    def tearDown(self):
        try:
            self.index.delete()
            client = connections.get_connection()
            client.indices.delete(index=ProjectDocument._index._name, ignore=[400, 404])
        except:
            pass

    def test_empty_query_returns_all_projects(self):
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_no_results_for_non_existent_title(self):
        url = reverse('project-list')
        response = self.client.get(url, {'search': 'nonexistent_project'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

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

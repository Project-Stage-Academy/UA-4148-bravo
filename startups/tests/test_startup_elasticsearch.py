from rest_framework.test import APITestCase
from rest_framework import status
from startups.models import Startup, Industry, Location
from startups.documents import StartupDocument
from django.urls import reverse
from elasticsearch_dsl.connections import connections
from django.conf import settings
import time
from rest_framework.test import APIClient
from users.models import UserRole, User
from elasticsearch import Elasticsearch

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
        # Встановити з’єднання з ES та ініціалізувати індекс лише один раз
        es_config = getattr(settings, 'ELASTICSEARCH_DSL', {}).get('default', {})
        hosts = es_config.get('hosts', 'http://localhost:9200')
        connections.configure(default={'hosts': hosts})
        StartupDocument.init()  # Це створить індекс і mapping

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
        # Видалити індекс перед кожним тестом
        try:
            client.indices.delete(index=StartupDocument._index._name, ignore=[400, 404])
        except Exception:
            pass

        # Створити індекс з mapping знову
        StartupDocument.init()

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

        # Індексувати документи
        for startup in Startup.objects.all():
            StartupDocument().update(startup)

        time.sleep(1)  # Дати час індексу оновитися

    def tearDown(self):
        client = connections.get_connection()
        try:
            client.indices.delete(index=StartupDocument._index._name, ignore=[400, 404])
        except Exception:
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

import time
from decimal import Decimal

from django.conf import settings
from django.urls import reverse
from elasticsearch_dsl.connections import connections
from rest_framework import status
from rest_framework.test import APITestCase
from elasticsearch_dsl import Index
from common.enums import Stage
from projects.documents import ProjectDocument
from projects.models import Project, Category
from startups.models import Location, Industry
from startups.models import Startup
from users.models import User, UserRole


class ProjectElasticsearchTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Configure Elasticsearch connection for tests
        es_config = getattr(settings, 'ELASTICSEARCH_DSL', {}).get('default', {})
        hosts = es_config.get('hosts', 'http://localhost:9200')
        connections.configure(default={'hosts': hosts})

    def setUp(self):
        self.index = Index('projects')
        # Try to delete the index if it exists, ignore errors
        try:
            self.index.delete()
        except:
            pass
        self.index.create()
        # Apply the document mapping to the index
        ProjectDocument._doc_type.mapping.save('projects')

        role = UserRole.objects.get(role=UserRole.Role.USER)
        self.user1 = User.objects.create_user(
            email='apistartup@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Startup',
            role=role,
        )
        self.user2 = User.objects.create_user(
            email='apistartup2@example.com',
            password='pass12345',
            first_name='Api2',
            last_name='Startup2',
            role=role,
        )
        self.client.force_authenticate(user=self.user1)
        self.client.force_authenticate(user=self.user2)

        self.industry1 = Industry.objects.create(name="Fintech")
        self.industry2 = Industry.objects.create(name="E-commerce")

        self.location1 = Location.objects.create(country="US")
        self.location2 = Location.objects.create(country="DE")

        self.startup1 = Startup.objects.create(
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

        self.startup2 = Startup.objects.create(
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

        self.category1 = Category.objects.create(name="Tech")
        self.category2 = Category.objects.create(name="Finance")

        self.project1 = Project.objects.create(
            startup=self.startup1,
            title="First Test Project",
            funding_goal=Decimal("10000.00"),
            current_funding=Decimal("0.00"),
            category=self.category1,
            email="project1@example.com"
        )
        self.project2 = Project.objects.create(
            startup=self.startup2,
            title="Second Test Project",
            funding_goal=Decimal("10000.00"),
            current_funding=Decimal("0.00"),
            category=self.category2,
            email="project2@example.com"
        )

        time.sleep(1)

    def tearDown(self):
        try:
            self.index.delete()
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
        url = reverse('projectdocument-list')
        response = self.client.get(url, {
            'category.name': 'Tech',
            'startup.company_name': 'Fintech Solutions'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "First Test Project")

    def test_invalid_filter_field_returns_bad_request(self):
        url = reverse('projectdocument-list')
        response = self.client.get(url, {'nonexistent_field': 'value'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

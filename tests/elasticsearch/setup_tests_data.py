from django.conf import settings
from django.test import TestCase
from elasticsearch_dsl.connections import connections
from rest_framework.test import APIClient

from common.enums import Stage
from tests.factories import UserFactory, IndustryFactory, LocationFactory, StartupFactory, \
    CategoryFactory, ProjectFactory


class BaseElasticsearchAPITestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        """
        Configure Elasticsearch connection before any tests run.
        """
        cls.user1 = UserFactory.create()
        cls.user2 = UserFactory.create()
        cls.industry1 = IndustryFactory.create(name="Fintech")
        cls.industry2 = IndustryFactory.create(name="E-commerce")
        cls.location1 = LocationFactory.create(country="US")
        cls.location2 = LocationFactory.create(country="DE")
        cls.startup1 = StartupFactory.create(
            user=cls.user1,
            industry=cls.industry1,
            location=cls.location1,
            company_name="Fintech Solutions",
            stage=Stage.IDEA,
        )
        cls.startup2 = StartupFactory.create(
            user=cls.user2,
            industry=cls.industry2,
            location=cls.location2,
            company_name="ShopFast",
            stage=Stage.MVP,
        )
        cls.category1 = CategoryFactory.create(name="Tech")
        cls.category2 = CategoryFactory.create(name="Finance")
        cls.project1 = ProjectFactory.create(
            startup=cls.startup1,
            category=cls.category1,
            title="First Test Project"
        )
        cls.project2 = ProjectFactory.create(
            startup=cls.startup2,
            category=cls.category2,
            title="Second Test Project"
        )

        es_config = getattr(settings, 'ELASTICSEARCH_DSL', {}).get('default', {})
        hosts = es_config.get('hosts', 'http://localhost:9200')
        connections.configure(default={'hosts': hosts})

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

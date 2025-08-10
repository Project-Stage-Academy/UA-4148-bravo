from unittest.mock import patch, MagicMock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from common.enums import Stage
from startups.models import Startup, Industry, Location
from users.models import UserRole, User


@patch('startups.documents.StartupDocument._doc_type.mapping.save', MagicMock())
@patch('elasticsearch_dsl.Index.create', MagicMock())
@patch('elasticsearch_dsl.Index.delete', MagicMock())
class StartupElasticsearchTests(APITestCase):

    def setUp(self):
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
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

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
            'stage': Stage.MVP,
            'location.country': 'DE'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "ShopFast")

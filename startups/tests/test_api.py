from unittest.mock import patch
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from startups.models import Startup
from startups.tests.test_setup import BaseStartupTestCase


class StartupAPITests(BaseStartupTestCase, APITestCase):

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch('django_elasticsearch_dsl.registries.registry.update')
    def test_create_startup(self, mock_update):
        url = reverse('startup-list')
        data = {
            'company_name': 'API Startup',
            'team_size': 10,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'email': 'startup@example.com'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_name'], 'API Startup')

    @patch('django_elasticsearch_dsl.registries.registry.update')
    def test_get_startup_list(self, mock_update):
        Startup.objects.create(
            user=self.user,
            company_name='ListStartup',
            founded_year=2019,
            industry=self.industry,
            location=self.location,
            email='list@example.com'
        )
        url = reverse('startup-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

from django.urls import reverse
from rest_framework import status

from startups.models import Startup
from startups.tests.test_setup import BaseStartupTestCase


class StartupAPITests(BaseStartupTestCase):

    def test_create_startup(self):
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
        print(response.status_code)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_name'], 'API Startup')

    def test_get_startup_list(self):
        Startup.objects.create(
            user=self.user,
            company_name='ListStartup',
            founded_year=2019,
            industry=self.industry,
            location=self.location
        )
        url = reverse('startup-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

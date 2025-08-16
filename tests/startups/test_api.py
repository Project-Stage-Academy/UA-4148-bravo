from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
from startups.models import Startup
from tests.startups.test_disable_signal_mixin import DisableElasticsearchSignalsMixin
from tests.test_base_case import BaseAPITestCase

class StartupAPITests(DisableElasticsearchSignalsMixin, BaseAPITestCase, TestCase):
    """ API tests for Startup endpoints (CRUD, filtering, search). """

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)  # Authenticate to avoid 401
        self.startup_data = {
            'company_name': 'Great',
            'team_size': 25,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'email': 'great@example.com',
        }
        self.url = reverse('startups-list')  # ViewSet list URL

    def test_create_startup_success(self):
        response = self.client.post(self.url, self.startup_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        startup = Startup.objects.get(pk=response.data['id'])
        self.assertEqual(startup.user, self.user)

    def test_delete_startup(self):
        """ Test deletion of a startup. """
        startup = self.get_or_create_startup(user=self.user, company_name='ToDelete', industry=self.industry, location=self.location)
        # DELETE должен идти на ViewSet endpoint, а не /detail/
        url_detail = reverse('startups-detail', args=[startup.pk])
        response = self.client.delete(url_detail)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Startup.objects.filter(pk=startup.pk).exists())



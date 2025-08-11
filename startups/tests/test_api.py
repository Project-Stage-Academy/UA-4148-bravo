from django.urls import reverse
from rest_framework import status

from tests.test_generic_case import DisableSignalMixinStartup, BaseAPITestCase


class StartupAPITests(DisableSignalMixinStartup, BaseAPITestCase):
    """
    Test suite for Startup API endpoints, including creation and retrieval of startups.
    """

    def test_create_startup(self):
        """
        Test that a startup can be successfully created via POST request to the startup-list endpoint.
        Verifies that the response status is HTTP 201 Created and the returned data matches the input.
        """
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

    def test_get_startup_list(self):
        """
        Test that the GET request to startup-list endpoint returns a list of startups,
        including at least one startup created in the test setup.
        Verifies response status is HTTP 200 OK and that at least one startup is returned.
        """
        self.create_startup(
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

from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from tests.test_base_case import BaseCompanyCreateAPITestCase
from startups.models import Startup, Industry, Location
from utils.authenticate_client import authenticate_client
from rest_framework.test import APIClient


@override_settings(SECURE_SSL_REDIRECT=False)
class StartupCreateAPITests(BaseCompanyCreateAPITestCase):
    """
    Tests for the startup creation API endpoint (POST /api/v1/startups/).
    """

    def setUp(self):
        """Override default setup to create a fresh user for each test."""
        super().setUp()
        self.user_for_creation = self.get_or_create_user(
            email="creator@example.com", first_name="Creator", last_name="User"
        )
        self.client = APIClient(enforce_csrf_checks=False)
        authenticate_client(self.client, self.user_for_creation)
        self.url = reverse('startup-list')
        self.industry, _ = Industry.objects.get_or_create(name="Testable Industry")
        self.location, _ = Location.objects.get_or_create(country="US")

    def get_valid_payload(self):
        """Returns a dictionary with valid data for creating a startup."""
        return {
            "company_name": "Innovative Tech Inc.",
            "description": "A new startup solving big problems.",
            "email": "contact@innovative-tech.com",
            "founded_year": 2024,
            "industry": self.industry.pk,
            "location": self.location.pk,
            "stage": "idea",
            "team_size": 5,
            "website": "https://innovative-tech.com"
        }

    def test_successful_startup_creation(self):
        """
        Ensure an authenticated user can create a new startup with valid data.
        """
        payload = self.get_valid_payload()
        self.assertEqual(Startup.objects.count(), 0)

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Startup.objects.count(), 1)
        
        startup = Startup.objects.first()
        self.assertEqual(startup.company_name, payload["company_name"])
        self.assertEqual(startup.user, self.user_for_creation)
        self.assertIn("id", response.data)

        self.assertEqual(Startup.objects.filter(user=self.user_for_creation).count(), 1)

    def test_unauthorized_creation_fails(self):
        """
        Ensure an unauthenticated user receives a 401 Unauthorized error.
        """
        client = self.client.__class__()
        payload = self.get_valid_payload()
        response = client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_with_duplicate_name_fails(self):
        """
        Ensure creating a startup with an already existing name fails with a
        400 Bad Request, even if attempted by a different, valid user.
        """
        payload = self.get_valid_payload()
        response1 = self.client.post(self.url, payload, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED, "First startup creation failed")

        second_user = self.get_or_create_user(
            email="secondcreator@example.com", first_name="Second", last_name="Creator"
        )
        authenticate_client(self.client, second_user)

        payload["email"] = "another-contact@innovative-tech.com" 
        response2 = self.client.post(self.url, payload, format='json')

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company_name", response2.data)
        self.assertIn("already exists", str(response2.data['company_name']))

    def test_user_cannot_create_more_than_one_startup(self):
        """
        Ensure a user who already owns a startup cannot create another one.
        """
        payload = self.get_valid_payload()

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payload["company_name"] = "Another Company"
        payload["email"] = "another-email@innovative-tech.com"
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You have already created a company profile", response.data['detail'])

    def test_creation_with_invalid_stage_fails(self):
        """
        Ensure creating a startup with an invalid 'stage' value fails validation.
        """
        payload = self.get_valid_payload()
        invalid_stage_value = "invalid_stage_value"
        payload["stage"] = invalid_stage_value
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stage", response.data)
        
        expected_error_message = f'"{invalid_stage_value}" is not a valid choice.'
        error_messages = [str(e) for e in response.data['stage']]
        self.assertIn(expected_error_message, error_messages)

    def test_creation_missing_required_fields_fails(self):
        """
        Ensure creating a startup without required fields like 'company_name' fails.
        """
        payload = self.get_valid_payload()
        del payload["company_name"]
        del payload["email"]

        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company_name", response.data)
        self.assertIn("email", response.data)
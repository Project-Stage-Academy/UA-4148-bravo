from django.urls import reverse
from rest_framework import status
from tests.test_base_case import BaseCompanyCreateAPITestCase
from startups.models import Startup, Industry, Location
from users.models import User

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
        self.client.force_authenticate(user=self.user_for_creation)
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
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Startup.objects.count(), 1)
        
        startup = Startup.objects.first()
        self.assertEqual(startup.company_name, payload["company_name"])
        self.assertEqual(startup.user, self.user_for_creation)
        self.assertIn("id", response.data)

    def test_unauthorized_creation_fails(self):
        """
        Ensure an unauthenticated user receives a 401 Unauthorized error.
        """
        self.client.logout()
        payload = self.get_valid_payload()
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_with_duplicate_name_fails(self):
        """
        Ensure creating a startup with an already existing name fails.
        """
        payload = self.get_valid_payload()

        self.client.post(self.url, payload, format='json')

        payload["email"] = "another-email@innovative-tech.com" 
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company_name", response.data)
        self.assertIn("already exists", str(response.data['company_name']))

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
        payload["stage"] = "invalid_stage_value"
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("stage", response.data)
        self.assertIn("is not a valid choice", str(response.data['stage']))

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
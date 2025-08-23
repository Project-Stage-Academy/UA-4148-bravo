from django.urls import reverse
from rest_framework import status
from tests.test_base_case import BaseAPITestCase
from investors.models import Investor
from startups.models import Industry, Location
from users.models import User

class InvestorCreateAPITests(BaseAPITestCase):
    """
    Tests for the investor creation API endpoint (POST /api/v1/investors/).
    """

    def setUp(self):
        """Override default setup to create a fresh user for each test."""
        super().setUp()
        self.user_for_creation = self.get_or_create_user(
            email="investor-creator@example.com", first_name="Creator", last_name="User"
        )
        self.client.force_authenticate(user=self.user_for_creation)
        self.url = reverse('investor-list')
        self.industry, _ = Industry.objects.get_or_create(name="Testable Industry")
        self.location, _ = Location.objects.get_or_create(country="US")

    def get_valid_payload(self):
        """Returns a dictionary with valid data for creating an investor."""
        return {
            "company_name": "Capital Ventures",
            "description": "Investing in the future of technology.",
            "email": "contact@capitalventures.com",
            "founded_year": 2020,
            "industry": self.industry.pk,
            "location": self.location.pk,
            "stage": "scale",
            "team_size": 20,
            "fund_size": "50000000.00",
            "website": "https://capitalventures.com"
        }

    def test_successful_investor_creation(self):
        """
        Ensure an authenticated user can create a new investor with valid data.
        """
        payload = self.get_valid_payload()
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Investor.objects.count(), 1)
        
        investor = Investor.objects.first()
        self.assertEqual(investor.company_name, payload["company_name"])
        self.assertEqual(investor.user, self.user_for_creation)
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
        Ensure creating an investor with an already existing name fails.
        """
        payload = self.get_valid_payload()
        self.client.post(self.url, payload, format='json')

        payload["email"] = "another-email@capitalventures.com"
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company_name", response.data)
        self.assertIn("already exists", str(response.data['company_name']))

    def test_user_cannot_create_more_than_one_investor(self):
        """
        Ensure a user who already owns an investor profile cannot create another one.
        """
        payload = self.get_valid_payload()
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        payload["company_name"] = "Another Investor Firm"
        payload["email"] = "another-email@capitalventures.com"
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You have already created a company profile", response.data['detail'])

    def test_creation_with_invalid_fund_size_fails(self):
        """
        Ensure creating an investor with a negative fund size fails validation.
        """
        payload = self.get_valid_payload()
        payload["fund_size"] = "-1000.00"
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fund_size", response.data)
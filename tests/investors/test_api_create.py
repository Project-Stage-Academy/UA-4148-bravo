from django.urls import reverse
from rest_framework import status
from tests.test_base_case import BaseCompanyCreateAPITestCase
from investors.models import Investor
from startups.models import Industry, Location
from utils.authenticate_client import authenticate_client
from django.test.utils import override_settings
from unittest.mock import patch

@override_settings(SECURE_SSL_REDIRECT=False)
class InvestorCreateAPITests(BaseCompanyCreateAPITestCase):
    """
    Tests for the investor creation API endpoint (POST /api/v1/investors/).
    """

    def setUp(self):
        """Override default setup to create a fresh user for each test."""
        super().setUp()
        self.user_for_creation = self.get_or_create_user(
            email="investor-creator@example.com", first_name="Creator", last_name="User"
        )
        authenticate_client(self.client, self.user_for_creation)
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

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_successful_investor_creation(self, mocked_permission):
        """
        Ensure an authenticated user can create a new investor with valid data.
        """
        payload = self.get_valid_payload()
        self.assertEqual(Investor.objects.count(), 0)

        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Investor.objects.count(), 1)

        investor = Investor.objects.first()
        self.assertEqual(investor.company_name, payload["company_name"])
        self.assertEqual(investor.user, self.user_for_creation)
        self.assertIn("id", response.data)

        self.assertEqual(Investor.objects.filter(user=self.user_for_creation).count(), 1)

    def test_unauthorized_creation_fails(self):
        """
        Ensure an unauthenticated user receives a 401 Unauthorized error.
        """
        self.client.logout()
        payload = self.get_valid_payload()
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_create_with_duplicate_name_fails(self, mocked_permission):
        """
        Ensure creating an investor with an already existing name fails.
        """
        payload = self.get_valid_payload()
        response1 = self.client.post(self.url, payload, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED, "First investor creation failed")

        second_user = self.get_or_create_user(
            email="second-investor-creator@example.com",
            first_name="Second",
            last_name="Creator"
        )
        authenticate_client(self.client, second_user)

        payload["email"] = "another-contact@capitalventures.com"
        response2 = self.client.post(self.url, payload, format='json')

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("company_name", response2.data)
        self.assertIn("already exists", str(response2.data['company_name']))

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_user_cannot_create_more_than_one_investor(self, mocked_permission):
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

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_creation_with_invalid_fund_size_fails(self, mocked_permission):
        """
        Ensure creating an investor with a negative fund size fails validation.
        """
        payload = self.get_valid_payload()
        payload["fund_size"] = "-1000.00"
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fund_size", response.data)

        self.assertIn("Ensure this value is greater than or equal to 0.", str(response.data["fund_size"]))

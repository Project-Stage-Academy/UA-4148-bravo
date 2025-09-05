from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from investors.views import InvestorListView
from users.models import User
from investors.models import Investor
from startups.models import Industry, Location
from django.contrib.auth import get_user_model
from utils.authenticate_client import authenticate_client
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.request import Request

@override_settings(APPEND_SLASH=False, SECURE_SSL_REDIRECT=False)
class InvestorAPITestCase(APITestCase):
    """
    TestCase for Investor API endpoints.
    Includes tests for listing investors, filtering by industry,
    and retrieving investor details.
    """

    def setUp(self):
        """
        Set up test data for Investor API tests.
        Creates:
        - A test user
        - An industry
        - A location
        - An investor linked to the user, industry, and location
        """
        User = get_user_model()
        self.user = User.objects.create_user(email="test@test.com", password="password123")

        self.industry = Industry.objects.create(name="Fintech")

        self.location = Location.objects.create(
            country="PL", 
            city="Warsaw", 
            region="Mazovia"
        )

        self.investor = Investor.objects.create(
            user=self.user,
            company_name="Fintech",
            industry=self.industry,
            location=self.location,
            team_size=10,
            stage="Seed",
            founded_year=2020,
        )
        authenticate_client(self.client, self.user)

    def test_list_investors(self):
        """
        Test that the investor list endpoint returns a successful response
        and at least one investor.
        """
        url = reverse("investor-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_filter_investors_by_industry(self):
        """
        Test filtering investors by industry.
        Ensures that the response contains only investors with the
        specified industry and that the company_name matches.
        """
        url = reverse("investor-list") + "?industry=Fintech"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for investor in response.json():
            self.assertEqual(investor["company_name"], "Fintech")

    def test_investor_detail(self):
        """
        Test retrieving the detail of a specific investor.
        Ensures that the response contains all required fields
        and correct investor data.
        """
        url = reverse("investor-detail", args=[self.investor.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()

        expected_fields = {
            "id",
            "company_name",
            "industry",
            "location",
            "team_size",
            "stage",
            "founded_year",
        }

        self.assertTrue(expected_fields.issubset(set(data.keys())))

        self.assertEqual(data["company_name"], "Fintech")
        self.assertEqual(data["team_size"], 10)
        self.assertEqual(data["stage"], "Seed")
        self.assertEqual(data["founded_year"], 2020)

    
    def test_valid_ordering_returns_sorted_list(self):
        """
        Ensure that a valid ordering field returns investors
        sorted according to the specified field.
        """
        url = reverse("investor-list")
        response = self.client.get(url, {"ordering": "company_name"})
        self.assertEqual(response.status_code, 200)
        company_names = [item["company_name"] for item in response.data]
        self.assertEqual(company_names, sorted(company_names))

    def test_invalid_ordering_field_raises_drf_validation_error(self):
        """
        Ensure that using an invalid ordering field
        raises DRF ValidationError with the correct message.
        """
        factory = APIRequestFactory()
        url = reverse("investor-list")
        wsgi_request = factory.get(url, {"ordering": "invalid_field"})
        wsgi_request.user = self.user 
        drf_request = Request(wsgi_request)
        view = InvestorListView()
        view.request = drf_request
        view.args = ()
        view.kwargs = {}

        with self.assertRaises(DRFValidationError) as context:
            view.get_queryset()

        self.assertIn('error', context.exception.detail)
        self.assertEqual(str(context.exception.detail['error']), 'Invalid ordering field')


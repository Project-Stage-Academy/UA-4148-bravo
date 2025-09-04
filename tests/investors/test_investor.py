from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User
from investors.models import Investor
from startups.models import Industry, Location
from django.contrib.auth import get_user_model


class InvestorAPITestCase(APITestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(email="test@test.com", password="password123")

        self.industry = Industry.objects.create(name="Tech")

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
            fund_size=1000000,
            team_size=10,
            stage="Seed",
            founded_year=2020,
        )
        self.client.force_authenticate(user=self.user)

    def test_list_investors(self):
        url = reverse("investor-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_filter_investors_by_industry(self):
        url = reverse("investor-list") + "?industry=Fintech"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]["company_name"], "Fintech")

    def test_investor_detail(self):
        url = reverse("investor-detail", args=[self.investor.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["company_name"], "Fintech")

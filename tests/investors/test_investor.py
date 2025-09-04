from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from users.models import User
from investors.models import Investor
from startups.models import Industry, Location

class InvestorAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com", password="pass1234")
        self.client.login(email="test@test.com", password="pass1234")

        industry = Industry.objects.create(name="Fintech")
        location = Location.objects.create(name="Warsaw")
        self.investor = Investor.objects.create(
            user=self.user,
            industry=industry,
            location=location,
            company_name="Fintech Capital",
            stage="MVP",
            team_size=15,
            fund_size=1000000
        )

    def test_list_investors(self):
        url = reverse("investor-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_filter_investors_by_industry(self):
        url = reverse("investor-list") + "?industry=Fintech"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]["company_name"], "Fintech Capital")

    def test_investor_detail(self):
        url = reverse("investor-detail", args=[self.investor.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["company_name"], "Fintech Capital")

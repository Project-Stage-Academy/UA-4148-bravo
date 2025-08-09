from django.urls import reverse
from rest_framework import status

from investors.models import Investor
from investors.tests.test_setup import BaseInvestorTestCase


class InvestorAPITests(BaseInvestorTestCase):

    def test_create_investor(self):
        url = reverse('investor-list')

        data = {
            'company_name': 'API Investor',
            'email': 'investor@api.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': 'mvp',
            'fund_size': '1000000.00',
        }

        response = self.client.post(url, data, format='json')

        if response.status_code != status.HTTP_201_CREATED:
            print("Response errors:", response.data)  # <- тут виведемо помилки валідації

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_name'], 'API Investor')
        self.assertEqual(response.data['email'], 'investor@api.com')

        investor = Investor.objects.get(pk=response.data['id'])
        self.assertEqual(investor.user, self.user)

        investor = Investor.objects.get(pk=response.data['id'])
        self.assertEqual(investor.user, self.user)

    def test_get_investor_list(self):
        Investor.objects.create(
            user=self.user,
            company_name='ListInvestor',
            founded_year=2019,
            industry=self.industry,
            location=self.location
        )
        url = reverse('investor-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_update_investor(self):
        investor = Investor.objects.create(
            user=self.user,
            company_name='OldName',
            founded_year=2020,
            industry=self.industry,
            location=self.location
        )
        url = reverse('investor-detail', args=[investor.id])
        data = {'company_name': 'UpdatedName'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'UpdatedName')

    def test_delete_investor(self):
        investor = Investor.objects.create(
            user=self.user,
            company_name='ToDelete',
            founded_year=2019,
            industry=self.industry,
            location=self.location
        )
        url = reverse('investor-detail', args=[investor.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

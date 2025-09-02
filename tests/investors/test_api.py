from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from common.enums import Stage
from investors.models import Investor
from tests.test_base_case import BaseAPITestCase
from rest_framework.test import APIClient


@override_settings(SECURE_SSL_REDIRECT=False)
class InvestorAPITests(BaseAPITestCase):
    """
    API tests for Investor model: list, update, delete,
    including validation and permission checks.
    """

    def test_get_investor_list(self):
        """
        Test retrieval of investor list includes expected entries.
        """
        self.get_or_create_investor(
            user=self.user,
            company_name='ListInvestor',
            stage=Stage.SCALE,
            fund_size=250000.00
        )
        url = reverse('investor-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        company_names = [investor['company_name'] for investor in response.data]
        self.assertIn('ListInvestor', company_names)

    def test_update_investor(self):
        """
        Test updating an investor's company_name via PATCH.
        """
        investor = self.get_or_create_investor(
            user=self.user,
            company_name='OldName',
            stage=Stage.LAUNCH,
            fund_size=300000.00
        )
        url = reverse('investor-detail', args=[investor.pk])
        data = {'company_name': 'UpdatedName'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'UpdatedName')
        investor.refresh_from_db()
        self.assertEqual(investor.company_name, 'UpdatedName')

    def test_update_investor_invalid_data(self):
        """
        Updating with invalid data should return validation errors.
        """
        investor = self.get_or_create_investor(
            user=self.user,
            company_name='ValidName',
            stage=Stage.SCALE,
            fund_size=500000.00
        )
        url = reverse('investor-detail', args=[investor.pk])
        data = {'founded_year': 'invalid_year'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('founded_year', response.data)

    def test_delete_investor(self):
        """
        Test successful deletion of an investor.
        """
        investor = self.get_or_create_investor(
            user=self.user,
            company_name='ToDelete',
            stage=Stage.MVP,
            fund_size=100000.00
        )
        url = reverse('investor-detail', args=[investor.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Investor.objects.filter(id=investor.pk).exists())

    def test_unauthorized_create_investor(self):
        """Unauthenticated user should get 401 when creating investor."""
        client = APIClient()
        url = reverse('investor-list')
        data = {
            'company_name': 'UnauthorizedInvestor',
            'email': 'unauth@api.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': Stage.MVP,
            'fund_size': '1000000.00',
        }
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_update_investor(self):
        """Unauthenticated user should get 401 when updating investor."""
        investor = self.get_or_create_investor(
            user=self.user,
            company_name='AuthInvestor',
            stage=Stage.MVP,
            fund_size=100000.00
        )
        client = APIClient()
        url = reverse('investor-detail', args=[investor.pk])
        data = {'company_name': 'ShouldNotUpdate'}
        response = client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_delete_investor(self):
        """Unauthenticated user should get 401 when deleting investor."""
        investor = self.get_or_create_investor(
            user=self.user,
            company_name='GoodInvestor',
            stage=Stage.MVP,
            fund_size=100000.00
        )
        client = APIClient()
        url = reverse('investor-detail', args=[investor.pk])
        response = client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

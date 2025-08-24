from django.urls import reverse, reverse_lazy
from rest_framework import status
from unittest.mock import patch
from common.enums import Stage
from investors.models import Investor
from tests.test_base_case import BaseAPITestCase


class InvestorAPITests(BaseAPITestCase):
    """
    API tests for Investor model: create, list, update, delete,
    including validation and permission checks.
    """

    @patch("users.permissions.IsInvestor.has_permission", return_value=True)
    @patch("users.permissions.IsInvestor.has_object_permission", return_value=True)
    def test_create_investor(self, mock_has_object_permission, mock_has_permission):
        """
        Test successful creation of an investor with valid data.
        """
        url = reverse_lazy('investor-list')
        data = {
            'company_name': 'API Investor',
            'email': 'investor@api.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': Stage.MVP,
            'fund_size': '1000000.00',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Errors: {response.data}")
        self.assertEqual(response.data['company_name'], data['company_name'])
        self.assertEqual(response.data['email'], data['email'])
        self.assertEqual(str(response.data['fund_size']), data['fund_size'])
        self.assertEqual(response.data['industry'], data['industry'])
        self.assertEqual(response.data['location'], data['location'])
        self.assertEqual(response.data['founded_year'], data['founded_year'])
        self.assertEqual(response.data['team_size'], data['team_size'])
        self.assertEqual(response.data['stage'], data['stage'])

        investor = Investor.objects.get(pk=response.data['id'])
        self.assertEqual(investor.user, self.user)

    @patch("users.permissions.IsInvestor.has_permission", return_value=True)
    @patch("users.permissions.IsInvestor.has_object_permission", return_value=True)
    def test_create_investor_missing_required_fields(self, mock_has_object_permission, mock_has_permission):
        """
        Creation should fail if required fields are missing.
        Missing company_name.
        """
        url = reverse('investor-list')
        data = {
            'email': 'badinvestor@api.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_name', response.data)

    @patch("users.permissions.IsInvestor.has_permission", return_value=True)
    @patch("users.permissions.IsInvestor.has_object_permission", return_value=True)
    def test_create_investor_invalid_data(self, mock_has_object_permission, mock_has_permission):
        """
        Creation should fail on invalid data types or values.
        Checked some expected error fields.
        """
        url = reverse('investor-list')
        data = {
            'company_name': 'BadInvestor',
            'email': 'bademail',
            'industry': 'not-an-id',
            'location': self.location.pk,
            'founded_year': 'not-a-year',
            'team_size': -5,
            'stage': 'invalid-stage',
            'fund_size': 'not-a-number',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('email', response.data)
        self.assertIn('industry', response.data)
        self.assertIn('founded_year', response.data)
        self.assertIn('team_size', response.data)
        self.assertIn('stage', response.data)
        self.assertIn('fund_size', response.data)

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
        """
        Unauthenticated user should NOT be able to create an investor.
        """
        self.client.logout()
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
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_update_investor(self):
        """
        Unauthenticated user should NOT be able to update an investor.
        """
        investor = self.get_or_create_investor(
            user=self.user,
            company_name='AuthInvestor',
            stage=Stage.MVP,
            fund_size=100000.00
        )
        self.client.logout()
        url = reverse('investor-detail', args=[investor.pk])
        data = {'company_name': 'ShouldNotUpdate'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthorized_delete_investor(self):
        """
        Unauthenticated user should NOT be able to delete an investor.
        """
        investor = self.get_or_create_investor(
            user=self.user,
            company_name='GoodInvestor',
            stage=Stage.MVP,
            fund_size=100000.00
        )
        self.client.logout()
        url = reverse('investor-detail', args=[investor.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

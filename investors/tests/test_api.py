from django.urls import reverse, reverse_lazy
from rest_framework import status
from common.enums import Stage
from investors.models import Investor
from tests.test_setup import BaseInvestorTestCase


class InvestorAPITests(BaseInvestorTestCase):
    """
    API tests for Investor model: create, list, update, delete,
    including validation and permission checks.
    """

    def test_create_investor(self):
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

    def test_create_investor_missing_required_fields(self):
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

    def test_create_investor_invalid_data(self):
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
        self.create_investor(
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
        company_names = [investor['company_name'] for investor in response.data]
        self.assertIn('ListInvestor', company_names)

    def test_update_investor(self):
        """
        Test updating an investor's company_name via PATCH.
        """
        investor = self.create_investor(
            user=self.user,
            company_name='OldName',
            founded_year=2020,
            industry=self.industry,
            location=self.location
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
        investor = self.create_investor(
            user=self.user,
            company_name='ValidName',
            founded_year=2020,
            industry=self.industry,
            location=self.location
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
        investor = self.create_investor(
            user=self.user,
            company_name='ToDelete',
            founded_year=2019,
            industry=self.industry,
            location=self.location
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
        investor = self.create_investor(
            user=self.user,
            company_name='AuthInvestor',
            founded_year=2020,
            industry=self.industry,
            location=self.location
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
        investor = self.create_investor(
            user=self.user,
            company_name='AuthInvestor',
            founded_year=2020,
            industry=self.industry,
            location=self.location
        )
        self.client.logout()
        url = reverse('investor-detail', args=[investor.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

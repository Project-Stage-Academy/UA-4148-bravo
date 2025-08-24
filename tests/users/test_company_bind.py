from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from startups.models import Startup, Industry, Location
from investors.models import Investor
from common.enums import Stage

User = get_user_model()


class CompanyBindingViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.industry = Industry.objects.create(
            name="Technology",
            description="Tech industry"
        )
        self.location = Location.objects.create(
            city="San Francisco",
            country="USA",
            region="California"
        )

        self.existing_startup = Startup.objects.create(
            company_name="Existing Startup",
            industry=self.industry,
            location=self.location,
            email="existing@startup.com",
            founded_year=2020,
            team_size=10,
            stage=Stage.MVP
        )

        self.existing_investor = Investor.objects.create(
            company_name="Existing Investor",
            industry=self.industry,
            location=self.location,
            email="existing@investor.com",
            founded_year=2010,
            team_size=20,
            stage=Stage.LAUNCH,
            fund_size=1000000
        )

        self.url = reverse('bind-company')

    def _authenticate_user(self):
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the endpoint"""
        response = self.client.post(self.url, {
            'company_name': 'Test Company',
            'company_type': 'startup'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bind_to_existing_startup(self):
        """Test binding to an existing startup"""
        self._authenticate_user()

        response = self.client.post(self.url, {
            'company_name': 'Existing Startup',
            'company_type': 'startup'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Successfully bound to existing startup: Existing Startup')
        self.assertEqual(response.data['company_type'], 'startup')

        self.user.refresh_from_db()
        self.assertTrue(hasattr(self.user, 'startup'))
        self.assertEqual(self.user.startup.company_name, 'Existing Startup')

    def test_bind_to_existing_investor(self):
        """Test binding to an existing investor"""
        self._authenticate_user()

        response = self.client.post(self.url, {
            'company_name': 'Existing Investor',
            'company_type': 'investor'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Successfully bound to existing investor: Existing Investor')
        self.assertEqual(response.data['company_type'], 'investor')

        self.user.refresh_from_db()
        self.assertTrue(hasattr(self.user, 'investor'))
        self.assertEqual(self.user.investor.company_name, 'Existing Investor')

    def test_create_new_startup(self):
        """Test creating and binding to a new startup"""
        self._authenticate_user()

        response = self.client.post(self.url, {
            'company_name': 'New Startup',
            'company_type': 'startup'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Successfully created and bound to new startup: New Startup')
        self.assertEqual(response.data['company_type'], 'startup')

        new_startup = Startup.objects.get(company_name='New Startup')
        self.assertEqual(new_startup.user, self.user)
        self.assertEqual(new_startup.stage, Stage.IDEA)
        self.assertEqual(new_startup.team_size, 1)

        self.user.refresh_from_db()
        self.assertTrue(hasattr(self.user, 'startup'))
        self.assertEqual(self.user.startup.company_name, 'New Startup')

    def test_create_new_investor(self):
        """Test creating and binding to a new investor"""
        self._authenticate_user()

        response = self.client.post(self.url, {
            'company_name': 'New Investor',
            'company_type': 'investor'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'Successfully created and bound to new investor: New Investor')
        self.assertEqual(response.data['company_type'], 'investor')

        new_investor = Investor.objects.get(company_name='New Investor')
        self.assertEqual(new_investor.user, self.user)
        self.assertEqual(new_investor.stage, Stage.MVP)
        self.assertEqual(new_investor.team_size, 1)
        self.assertEqual(new_investor.fund_size, 0)

        self.user.refresh_from_db()
        self.assertTrue(hasattr(self.user, 'investor'))
        self.assertEqual(self.user.investor.company_name, 'New Investor')

    def test_case_insensitive_company_name_matching(self):
        """Test that company name matching is case insensitive"""
        self._authenticate_user()

        response = self.client.post(self.url, {
            'company_name': 'EXISTING startup',  # Different case
            'company_type': 'startup'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Successfully bound to existing startup: EXISTING startup')

        self.user.refresh_from_db()
        self.assertTrue(hasattr(self.user, 'startup'))
        self.assertEqual(self.user.startup.company_name, 'Existing Startup')

    def test_cannot_bind_to_company_already_associated_with_user(self):
        """Test that a company already associated with a user cannot be bound again"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123'
        )
        self.existing_startup.user = other_user
        self.existing_startup.save()

        self._authenticate_user()

        response = self.client.post(self.url, {
            'company_name': 'Existing Startup',
            'company_type': 'startup'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Startup is already associated with another user.')

        self.user.refresh_from_db()
        self.assertFalse(hasattr(self.user, 'startup'))

    def test_cannot_bind_multiple_times(self):
        """Test that a user cannot bind to multiple companies"""
        self._authenticate_user()

        response1 = self.client.post(self.url, {
            'company_name': 'Existing Startup',
            'company_type': 'startup'
        })
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(self.url, {
            'company_name': 'Another Startup',
            'company_type': 'startup'
        })

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response2.data['error'], 'User is already bound to a company.')

    def test_cannot_bind_to_different_company_types_after_binding(self):
        """Test that a user cannot bind to a different company type after already binding"""
        self._authenticate_user()

        response1 = self.client.post(self.url, {
            'company_name': 'Existing Startup',
            'company_type': 'startup'
        })
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(self.url, {
            'company_name': 'Existing Investor',
            'company_type': 'investor'
        })

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response2.data['error'], 'User is already bound to a company.')

    def test_default_industry_and_location_creation(self):
        """Test that default industry and location are created for new companies"""
        Industry.objects.filter(name="Unknown").delete()
        Location.objects.filter(city="Unknown", country="Unknown").delete()

        self._authenticate_user()

        response = self.client.post(self.url, {
            'company_name': 'Test Startup',
            'company_type': 'startup'
        })

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        default_industry = Industry.objects.get(name="Unknown")
        default_location = Location.objects.get(city="Unknown", country="Unknown")

        new_startup = Startup.objects.get(company_name='Test Startup')
        self.assertEqual(new_startup.industry, default_industry)
        self.assertEqual(new_startup.location, default_location)

    def test_transaction_rollback_on_error(self):
        """Test that transaction is rolled back if an error occurs during creation"""
        self._authenticate_user()

        original_create = Startup.objects.create

        def mock_create(*args, **kwargs):
            if kwargs.get('company_name') == 'Error Startup':
                raise ValueError("Simulated error")
            return original_create(*args, **kwargs)

        Startup.objects.create = mock_create

        try:
            response = self.client.post(self.url, {
                'company_name': 'Error Startup',
                'company_type': 'startup'
            })

            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

            with self.assertRaises(Startup.DoesNotExist):
                Startup.objects.get(company_name='Error Startup')

            self.user.refresh_from_db()
            self.assertFalse(hasattr(self.user, 'startup'))
            self.assertFalse(hasattr(self.user, 'investor'))

        finally:
            Startup.objects.create = original_create

    def test_validation_error_handling(self):
        """Test that validation errors are properly handled"""
        self._authenticate_user()

        response = self.client.post(self.url, {
            'company_name': '',
            'company_type': 'startup'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_name', response.data)

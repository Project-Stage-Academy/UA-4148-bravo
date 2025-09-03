from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch
from tests.factories import (
    UserFactory,
    IndustryFactory,
    LocationFactory,
    StartupFactory,
    InvestorFactory
)
from users.models import User
from startups.models import Startup, Industry, Location, Stage
from investors.models import Investor
from utils.authenticate_client import authenticate_client

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class CompanyBindingViewTests(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.url = reverse('bind_company')

        self.user = UserFactory.create()
        self.user1 = UserFactory.create(email='user1@example.com')
        self.user2 = UserFactory.create(email='user2@example.com')
        self.other_user = UserFactory.create(email='other@example.com')

        self.industry = IndustryFactory.create(name="Fintech")
        self.location = LocationFactory.create(country="US")

        self.startup = StartupFactory.create(
            user=self.user1,
            industry=self.industry,
            location=self.location,
            company_name="Existing Startup",
            stage=Stage.MVP,
        )
        self.investor = InvestorFactory.create(
            user=self.user2,
            industry=self.industry,
            location=self.location,
            company_name="Existing Investor",
            stage=Stage.LAUNCH,
        )

        self.client = APIClient(enforce_csrf_checks=False)
        self.csrf_url = reverse("csrf_init")

    def startup_payload(self, name="New Startup"):
        return {"company_name": name, "company_type": "startup"}

    def investor_payload(self, name="New Investor"):
        return {"company_name": name, "company_type": "investor"}

    def test_bind_to_new_startup_success(self):
        """Test successful creation and binding to new startup"""
        authenticate_client(self.client, self.user)

        response = self.client.post(self.url, self.startup_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_type'], 'startup')
        self.assertIn('company_id', response.data)
        self.assertIn('Successfully created and bound to new startup', response.data['message'])

        new_startup = Startup.objects.get(company_name='New Startup')
        self.assertEqual(new_startup.user, self.user)
        self.assertEqual(new_startup.email, self.user.email)
        self.assertEqual(new_startup.stage, Stage.IDEA)
        self.assertEqual(new_startup.industry.name, "Unknown")
        self.assertEqual(new_startup.location.city, "Unknown")

    def test_bind_to_new_investor_success(self):
        """Test successful creation and binding to new investor"""
        authenticate_client(self.client, self.user)

        response = self.client.post(self.url, self.investor_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_type'], 'investor')
        self.assertIn('company_id', response.data)
        self.assertIn('Successfully created and bound to new investor', response.data['message'])

        new_investor = Investor.objects.get(company_name='New Investor')
        self.assertEqual(new_investor.user, self.user)
        self.assertEqual(new_investor.email, self.user.email)
        self.assertEqual(new_investor.stage, Stage.MVP)
        self.assertEqual(new_investor.fund_size, 0)
        self.assertEqual(new_investor.industry.name, "Unknown")
        self.assertEqual(new_investor.location.city, "Unknown")

    def test_bind_to_existing_company_with_different_user(self):
        """Test binding to existing company that has a different user"""
        authenticate_client(self.client, self.user)

        response = self.client.post(
            self.url,
            self.startup_payload(name='Existing Startup'),
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('company_name', response.data['error'])
        self.assertIn('already exists', str(response.data['error']['company_name'][0]))

    def test_user_already_bound_to_startup(self):
        """Test binding when user is already bound to a startup"""
        Startup.objects.create(
            user=self.user,
            company_name='My Startup',
            industry=self.industry,
            location=self.location,
            email=f"{self.user.email}.startup",
            founded_year=2020,
            team_size=5,
            stage=Stage.IDEA
        )

        authenticate_client(self.client, self.user)

        response = self.client.post(
            self.url,
            self.startup_payload(name='Another Company'),
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already bound', response.data['error'])

    def test_user_already_bound_to_investor(self):
        """Test binding when user is already bound to an investor"""
        Investor.objects.create(
            user=self.user,
            company_name='My Investor',
            industry=self.industry,
            location=self.location,
            email=f"{self.user.email}.investor",
            founded_year=2015,
            team_size=3,
            stage=Stage.MVP,
            fund_size=500000
        )

        authenticate_client(self.client, self.user)

        response = self.client.post(
            self.url,
            self.investor_payload(name='Another Company'),
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already bound', response.data['error'])

    def test_invalid_company_type(self):
        """Test binding with invalid company type"""
        data = {
            'company_name': 'Test Company',
            'company_type': 'invalid_type'
        }

        authenticate_client(self.client, self.user)

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_type', response.data['error'])

    def test_missing_company_name(self):
        """Test binding with missing company name"""
        data = {
            'company_type': 'startup'
        }

        authenticate_client(self.client, self.user)

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('company_name', response.data['error'])

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the endpoint"""
        client = APIClient(enforce_csrf_checks=False)

        data = {
            'company_name': 'Test Company',
            'company_type': 'startup'
        }
        response = client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('startups.models.Startup.objects.create')
    def test_startup_creation_failure(self, mock_create):
        """Test handling of startup creation failure"""
        mock_create.side_effect = Exception("Creation failed")

        authenticate_client(self.client, self.user)

        response = self.client.post(
            self.url,
            self.startup_payload(name='New Startup'),
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('unexpected error', response.data['error'])

    @patch('investors.models.Investor.objects.create')
    def test_investor_creation_failure(self, mock_create):
        """Test handling of investor creation failure"""
        mock_create.side_effect = Exception("Creation failed")

        authenticate_client(self.client, self.user)

        response = self.client.post(self.url, self.investor_payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('unexpected error', response.data['error'])

    def test_default_industry_and_location_creation(self):
        """Test that default industry and location are created for new companies"""
        Industry.objects.filter(name="Unknown").delete()
        Location.objects.filter(city="Unknown").delete()

        authenticate_client(self.client, self.user)

        response = self.client.post(
            self.url,
            self.startup_payload(name='New Test Company'),
            format="json"
        )

        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
            self.fail(f"Failed to create company: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Industry.objects.filter(name="Unknown").exists())

        default_location = Location.objects.get(city="Unknown")
        self.assertIsNotNone(default_location.country)
        self.assertEqual(str(default_location.country), "US")

        default_industry = Industry.objects.get(name="Unknown")
        new_startup = Startup.objects.get(company_name='New Test Company')

        self.assertEqual(new_startup.industry, default_industry)
        self.assertEqual(new_startup.location, default_location)

    def test_transaction_atomicity_on_creation_failure(self):
        """Test that the transaction is atomic (rolls back on error)"""
        original_startup_count = Startup.objects.count()

        with patch('startups.models.Startup.objects.create') as mock_create:
            mock_create.side_effect = Exception("Creation failed")

            authenticate_client(self.client, self.user)

            response = self.client.post(
                self.url,
                self.startup_payload(name='Should Not Exist'),
                format="json"
            )

            self.assertEqual(Startup.objects.count(), original_startup_count)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_company_name_uniqueness_enforcement(self):
        """Test that company name uniqueness is enforced"""
        authenticate_client(self.client, self.user)
        response1 = self.client.post(self.url, self.startup_payload(name='Unique Company'), format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        another_user = User.objects.create_user(
            email='another_unique@example.com',
            password='anotherpass123',
            first_name='Another',
            last_name='User'
        )

        another_client = APIClient(enforce_csrf_checks=False)
        authenticate_client(another_client, another_user)
        response2 = another_client.post(self.url, self.startup_payload(name='Unique Company'), format="json")
        self.assertEqual(
            response2.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Expected 400, got {response2.status_code}, data={getattr(response2, 'data', None)}"
        )

        self.assertIn('company_name', response2.data.get('error', {}))
        error_text = str(response2.data['error'])
        self.assertTrue(any(keyword in error_text for keyword in ['company', 'name', 'exists', 'unique']),
                        f"Error should be about company name uniqueness: {error_text}")

    def test_email_uniqueness_enforcement(self):
        """Test that a user cannot bind a second company with the same email"""
        authenticate_client(self.client, self.user)

        data1 = {
            'company_name': 'First Company',
            'company_type': 'startup'
        }
        response1 = self.client.post(self.url, data1, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        data2 = {
            'company_name': 'Second Company',
            'company_type': 'startup'
        }
        response2 = self.client.post(self.url, data2, format='json')

        self.assertEqual(
            response2.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Expected 400, got {response2.status_code}, data={getattr(response2, 'data', None)}"
        )
        error_text = str(response2.data.get('error', ''))
        self.assertIn('already bound', error_text.lower(), f"Unexpected error message: {error_text}")

    def test_bind_to_company_with_same_name_different_case(self):
        """Test binding to company with same name but different case"""
        Startup.objects.create(
            user=self.other_user,
            company_name='Test Company',
            industry=self.industry,
            location=self.location,
            email='test@example.com',
            founded_year=2020,
            team_size=5,
            stage=Stage.IDEA
        )

        authenticate_client(self.client, self.user)

        response = self.client.post(
            self.url,
            self.startup_payload(name='test company'),
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_cannot_have_both_startup_and_investor(self):
        """Test that user cannot be bound to both startup and investor"""
        authenticate_client(self.client, self.user)

        response1 = self.client.post(
            self.url,
            self.startup_payload(name='TechNova'),
            format="json"
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        response2 = self.client.post(
            self.url,
            self.investor_payload(name='ShortDesc'),
            format="json"
        )

        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response2.data)
        self.assertEqual('User is already bound to a company.', str(response2.data['error']))

from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from investors.models import Investor
from investors.serializers import InvestorSerializer
from startups.models import Industry, Location, Startup
from startups.serializers import StartupSerializer
from users.models import UserRole

User = get_user_model()


# ─────────────────────────────────────────────────────────────
# SERIALIZER TESTS
# ─────────────────────────────────────────────────────────────

class StartupSerializerTests(TestCase):
    def setUp(self):
        self.industry = Industry.objects.create(name='AI')
        self.location = Location.objects.create(city='New York', region='NY', country='US')

        role = UserRole.objects.get(role='user')
        self.user = User.objects.create_user(
            email='apiinvestor@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Investor',
            role=role,
        )

    def test_valid_startup_data(self):
        data = {
            'company_name': 'TechNova',
            'description': 'AI-powered analytics',
            'industry': self.industry.id,
            'country': 'US',
            'website': 'https://technova.ai',
            'email': 'contact@technova.ai',
            'phone': '+1234567890',
            'contact_person': 'John Smith',
            'location': self.location.id,
            'status': 'Active',
            'stage': 'idea',
            'social_links': {
                'linkedin': 'https://linkedin.com/in/technova',
                'twitter': 'https://twitter.com/technova'
            },
            'is_participant': True,
            'founded_at': date(2020, 5, 1),
            'team_size': 10,
            'is_active': True,
            'user': self.user.id
        }
        serializer = StartupSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_empty_company_name_should_fail(self):
        data = {
            'company_name': '   ',
            'team_size': 5,
            'website': 'https://example.com',
            'email': 'test@example.com'
        }
        serializer = StartupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('company_name', serializer.errors)

    def test_missing_contact_should_fail(self):
        data = {
            'company_name': 'ValidName',
            'team_size': 5,
            'website': '',
            'email': ''
        }
        serializer = StartupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('contact', serializer.errors)

    def test_team_size_too_small_should_fail(self):
        data = {
            'company_name': 'ValidName',
            'team_size': 0,
            'website': 'https://example.com',
            'email': 'test@example.com'
        }
        serializer = StartupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('team_size', serializer.errors)

    def test_invalid_social_links_should_fail(self):
        data = {
            'company_name': 'ValidName',
            'team_size': 5,
            'website': 'https://example.com',
            'email': 'test@example.com',
            'social_links': {
                'linkedin': 'https://notlinkedin.com/profile',
                'unknown': 'https://example.com'
            }
        }
        serializer = StartupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('social_links', serializer.errors)

        errors = serializer.errors['social_links']
        self.assertIn("Invalid domain for platform 'linkedin'", errors.get('linkedin', ''))
        self.assertIn("Platform 'unknown' is not supported.", errors.get('unknown', ''))


class InvestorSerializerTests(TestCase):
    def setUp(self):
        role = UserRole.objects.get(role='user')

        self.user = User.objects.create_user(
            email='apiinvestor@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Investor',
            role=role,
        )

    def test_valid_investor_data(self):
        data = {
            'company_name': 'CapitalBridge',
            'email': 'jane@example.com',
            'country': 'US',
            'fund_size': '1000000.00',
            'stage': 'mvp',
            'is_active': True,
            'user': self.user.id
        }
        serializer = InvestorSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_empty_company_name_should_fail(self):
        data = {
            'company_name': '   ',
            'email': 'jane@example.com',
            'user': self.user.id
        }
        serializer = InvestorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('company_name', serializer.errors)

    def test_invalid_social_links_should_fail(self):
        data = {
            'company_name': 'CapitalBridge',
            'email': 'jane@example.com',
            'user': self.user.id,
            'social_links': {
                'facebook': 'https://notfacebook.com/page',
                'unknown': 'https://example.com'
            }
        }
        serializer = InvestorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('social_links', serializer.errors)

        errors = serializer.errors['social_links']
        self.assertIn("Invalid domain for platform 'facebook'", errors.get('facebook', ''))
        self.assertIn("Platform 'unknown' is not supported.", errors.get('unknown', ''))


# ─────────────────────────────────────────────────────────────
# MODEL CLEAN() TESTS
# ─────────────────────────────────────────────────────────────

class StartupModelCleanTests(TestCase):
    def setUp(self):
        role = UserRole.objects.get(role='user')

        self.user = User.objects.create_user(
            email='apiinvestor@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Investor',
            role=role,
        )

        self.industry = Industry.objects.create(name="Technology")
        self.location = Location.objects.create(country="US")

    def test_invalid_social_links_clean_should_raise(self):
        startup = Startup(
            user=self.user,
            company_name='CleanTech',
            founded_year=2022,
            industry=self.industry,
            location=self.location,
            social_links={
                'linkedin': 'https://notlinkedin.com/profile',
                'unknown': 'https://example.com'
            }
        )
        with self.assertRaises(ValidationError) as context:
            startup.clean()
        self.assertIn('social_links', context.exception.message_dict)


class InvestorModelCleanTests(TestCase):
    def setUp(self):
        role = UserRole.objects.get(role='user')

        self.user = User.objects.create_user(
            email='apiinvestor@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Investor',
            role=role,
        )

        self.industry = Industry.objects.create(name="Technology")
        self.location = Location.objects.create(country="US")

    def test_valid_clean_should_pass(self):
        investor = Investor(
            user=self.user,
            company_name='InvestX',
            founded_year=2020,
            industry=self.industry,
            location=self.location,
            fund_size=1000000,
            stage='mvp',
            social_links={
                'linkedin': 'https://linkedin.com/in/investx'
            }
        )
        try:
            investor.clean()  # should not raise
        except ValidationError:
            self.fail("Investor.clean() raised ValidationError unexpectedly")


# ─────────────────────────────────────────────────────────────
# API TESTS
# ─────────────────────────────────────────────────────────────

class StartupAPITests(APITestCase):
    def setUp(self):
        role = UserRole.objects.get(role='user')

        self.user = User.objects.create_user(
            email='apiinvestor@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Investor',
            role=role,
        )

        self.industry = Industry.objects.create(name="Technology")
        self.location = Location.objects.create(country="US")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_startup(self):
        url = reverse('startup-list')
        data = {
            'company_name': 'API Startup',
            'team_size': 5,
            'website': 'https://api-startup.com',
            'email': 'contact@api-startup.com',
            'user': self.user.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_name'], 'API Startup')

    def test_get_startup_list(self):
        Startup.objects.create(
            user=self.user,
            company_name='ListStartup',
            founded_year=2022,
            industry=self.industry,
            location=self.location,
        )
        url = reverse('startup-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)


class InvestorAPITests(APITestCase):
    def setUp(self):
        role = UserRole.objects.get(role='user')

        self.user = User.objects.create_user(
            email='apiinvestor@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Investor',
            role=role,
        )

        self.industry = Industry.objects.create(name="Technology")
        self.location = Location.objects.create(country="US")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_investor(self):
        url = reverse('investor-list')
        data = {
            'company_name': 'API Investor',
            'email': 'investor@api.com',
            'user': self.user.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_name'], 'API Investor')

    def test_get_investor_list(self):
        Investor.objects.create(
            user=self.user,
            company_name='ListInvestor',
            founded_year=2019,
            industry=self.industry,
            location=self.location,
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
        self.assertEqual(response.status_code)

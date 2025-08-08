from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from projects.models import Project, Category
from startups.models import Startup, Industry, Location
from users.models import UserRole

User = get_user_model()


class ProjectModelCleanTests(TestCase):
    def setUp(self):
        role = UserRole.objects.get_or_create(role='user')

        self.user = User.objects.create_user(
            email='apiinvestor@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Startup',
            role=role,
        )

        self.industry = Industry.objects.create(name="Technology")
        self.location = Location.objects.create(country="US")
        self.startup = Startup.objects.create(
            user=self.user,
            company_name='CleanStartup',
            industry=self.industry,
            location=self.location,
            founded_year=2010
        )
        self.category = Category.objects.create(name='CleanTech')

    def test_clean_should_raise_for_invalid_funding(self):
        project = Project(
            startup=self.startup,
            title='BadFunding',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('20000.00'),
            category=self.category,
            email='bad@example.com'
        )
        with self.assertRaises(ValidationError) as context:
            project.clean()
        self.assertIn('current_funding', context.exception.message_dict)

    def test_clean_should_raise_for_missing_plan(self):
        project = Project(
            startup=self.startup,
            title='MissingPlan',
            status='completed',
            funding_goal=Decimal('50000.00'),
            current_funding=Decimal('10000.00'),
            category=self.category,
            email='missing@example.com'
        )
        with self.assertRaises(ValidationError) as context:
            project.clean()
        self.assertIn('business_plan', context.exception.message_dict)

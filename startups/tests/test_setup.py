from django.test import TestCase
from django.contrib.auth import get_user_model
from startups.models import Industry, Location


class BaseStartupTestCase(TestCase):
    """
    Base test case for Startup-related tests.
    Creates a default user, industry, and location for reuse in child tests.
    """

    def setUp(self):
        # Create a test user
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            password='password123'
        )

        # Create an industry instance
        self.industry = Industry.objects.create(name='Technology')

        # Create a location instance
        self.location = Location.objects.create(name='Kyiv', country='UA')

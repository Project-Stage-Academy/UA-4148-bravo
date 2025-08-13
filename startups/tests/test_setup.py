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
        # This user will be used in all inherited test cases
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            password='password123'
        )

        # Create an industry instance
        # The "name" field exists in Industry model
        self.industry = Industry.objects.create(name='Technology')

        # Create a location instance
        # IMPORTANT: Adjusted to match the actual Location model fields
        # In our case, there is no "name" field, but there is "city" and "country"
        self.location = Location.objects.create(
            country='UA',
            city='Kyiv'
        )


from django.core.exceptions import ValidationError
from startups.models import Location
from tests.test_base_case import BaseAPITestCase


class LocationModelCleanTests(BaseAPITestCase):
    """Tests for Location model clean() validations."""

    def test_valid_location_should_pass(self):
        """
        Test that a Location instance with valid fields
        passes the full_clean() validation without errors.
        """
        location = Location(
            country='US',
            region='California',
            city='San Francisco',
            address_line='Market Street',
            postal_code='94103'
        )
        try:
            location.full_clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly.")

    def test_postal_code_too_short_should_raise(self):
        """
        Test that a postal code shorter than 3 characters
        raises a ValidationError on clean().
        """
        location = Location(country='US', postal_code='12')
        with self.assertRaises(ValidationError) as context:
            location.clean()
        self.assertIn('postal_code', context.exception.message_dict)

    def test_postal_code_invalid_chars_should_raise(self):
        """
        Test that a postal code containing invalid characters
        raises a ValidationError on clean().
        """
        location = Location(country='US', postal_code='@@@')
        with self.assertRaises(ValidationError) as context:
            location.clean()
        self.assertIn('postal_code', context.exception.message_dict)

    def test_city_with_invalid_chars_should_raise(self):
        """
        Test that a city name containing non-Latin characters
        raises a ValidationError on clean().
        """
        location = Location(country='US', city='Kyїv')
        with self.assertRaises(ValidationError) as context:
            location.clean()
        self.assertIn('city', context.exception.message_dict)

    def test_address_line_requires_city_and_region(self):
        """
        Test that providing an address_line without city and region
        raises a ValidationError indicating those fields are required.
        """
        location = Location(
            country='US',
            address_line='Main Street'
        )
        with self.assertRaises(ValidationError) as context:
            location.clean()
        self.assertIn('city', context.exception.message_dict)
        self.assertIn('region', context.exception.message_dict)

    def test_city_requires_region(self):
        """
        Test that providing a city without a region
        raises a ValidationError indicating region is required.
        """
        location = Location(country='US', city='Chicago')
        with self.assertRaises(ValidationError) as context:
            location.clean()
        self.assertIn('region', context.exception.message_dict)

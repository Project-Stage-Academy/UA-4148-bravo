from django.core.exceptions import ValidationError
from startups.models import Location
from tests.test_base_case import BaseAPITestCase


class LocationModelCleanTests(BaseAPITestCase):
    """Tests for Location model clean()/full_clean() validations."""

    def test_valid_location_should_pass(self):
        """
        Full valid dataset should pass full_clean() without errors.
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
        Postal code shorter than 3 characters should raise ValidationError.
        """
        location = Location(country='US', postal_code='12')
        with self.assertRaises(ValidationError) as context:
            location.clean()
        self.assertIn('postal_code', context.exception.message_dict)

    def test_postal_code_invalid_chars_should_raise(self):
        """
        Postal code with invalid characters should raise ValidationError.
        """
        location = Location(country='US', postal_code='@@@')
        with self.assertRaises(ValidationError) as context:
            location.clean()
        self.assertIn('postal_code', context.exception.message_dict)

    def test_city_with_invalid_chars_should_raise(self):
        """
        City with non-Latin characters should raise ValidationError.
        """
        location = Location(country='US', city='Kyїv')
        with self.assertRaises(ValidationError) as context:
            location.clean()
        self.assertIn('city', context.exception.message_dict)

    def test_address_line_requires_city_and_region(self):
        """
        address_line requires both city and region to be present.
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
        City provided without region should raise ValidationError.
        """
        location = Location(country='US', city='Chicago')
        with self.assertRaises(ValidationError) as context:
            location.clean()
        self.assertIn('region', context.exception.message_dict)

    def test_location_clean_valid_letters_only(self):
        """
        Additional positive case from legacy tests:
        postal_code/address_line consisting of Latin letters and spaces should pass.
        """
        location = Location(
            country="US",
            city="New York",
            region="NY",
            postal_code="ABCDE",
            address_line="Main Street"
        )
        try:
            location.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly for valid latin-only data.")


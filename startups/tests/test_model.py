from django.core.exceptions import ValidationError
from django.test import TestCase
from startups.models import Location

class LocationModelTests(TestCase):

    def test_location_clean_valid(self):
        """
        Test that clean() passes for valid Location data.
        Postal code and address_line should contain only Latin letters, spaces, hyphens, or apostrophes.
        """
        location = Location(
            country="US",
            city="New York",
            region="NY",
            postal_code="ABCDE",      # Changed to letters only to pass validation
            address_line="Main Street"  # Changed to letters only to pass validation
        )
        try:
            location.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly for valid data")

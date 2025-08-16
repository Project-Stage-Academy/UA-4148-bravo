# tests/startups/test_location_model.py
from django.core.exceptions import ValidationError
from django.test import TestCase
from startups.models import Location
from tests.startups.test_disable_signal_mixin import DisableElasticsearchSignalsMixin
from tests.test_base_case import BaseAPITestCase


class LocationModelCleanTests(DisableElasticsearchSignalsMixin, BaseAPITestCase, TestCase):
    """Tests for Location.clean() / full_clean() validations."""

    def test_valid_location_should_pass(self):
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
        location = Location(country='US', postal_code='12')
        with self.assertRaises(ValidationError) as context:
            location.clean()
        self.assertIn('postal_code', context.exception.message_dict)




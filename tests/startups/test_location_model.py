from django.core.exceptions import ValidationError as DjangoValidationError
from startups.models import Location
from tests.test_base_case import BaseAPITestCase
from unittest.mock import patch
from startups.documents import StartupDocument


class LocationModelCleanTests(BaseAPITestCase):
    """Tests for Location model validation and constraints."""

    @classmethod
    def setUpClass(cls):
        # Mock the update method of StartupDocument to prevent Elasticsearch calls
        cls.update_patcher = patch.object(StartupDocument, 'update', lambda self, instance, **kwargs: None)
        cls.update_patcher.start()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.update_patcher.stop()
        super().tearDownClass()

    def test_create_location_success(self):
        """Location can be created successfully with valid data."""
        location = Location.objects.create(
            country="US",
            region="California",
            city="San Francisco",
            address_line="Market Street",
            postal_code="94103"
        )
        self.assertEqual(location.city, "San Francisco")
        self.assertTrue(location.pk is not None)

    def test_location_name_not_empty(self):
        """City name cannot be empty."""
        with self.assertRaises(DjangoValidationError):
            location = Location(
                country="US",
                region="California",
                city="",
                postal_code="94103"
            )
            location.full_clean()
            location.save()

    def test_postal_code_format(self):
        """Postal code must be at least 3 characters."""
        with self.assertRaises(DjangoValidationError):
            location = Location(country="US", postal_code="12")
            location.full_clean()
            location.save()

    def test_invalid_postal_code_chars(self):
        """Postal code cannot contain invalid characters."""
        with self.assertRaises(DjangoValidationError):
            location = Location(country="US", postal_code="@@@")
            location.full_clean()
            location.save()

    def test_city_requires_region(self):
        """City without region should raise ValidationError."""
        with self.assertRaises(DjangoValidationError):
            location = Location(country="US", city="Chicago")
            location.full_clean()
            location.save()

    def test_address_requires_city_and_region(self):
        """Address line without city and region raises ValidationError."""
        with self.assertRaises(DjangoValidationError):
            location = Location(country="US", address_line="Main Street")
            location.full_clean()
            location.save()

    def test_location_str_method(self):
        """__str__ returns formatted location string."""
        location = Location.objects.create(
            country="US",
            region="California",
            city="Los Angeles",
            address_line="Sunset Blvd",
            postal_code="90028"
        )
        self.assertEqual(str(location), "Los Angeles, California, US")

    def test_location_update_fields(self):
        """Updating location fields works correctly."""
        location = Location.objects.create(
            country="US",
            region="California",
            city="OldCity",
            postal_code="90001"
        )
        location.city = "NewCity"
        location.full_clean()
        location.save()
        self.assertEqual(Location.objects.get(pk=location.pk).city, "NewCity")

    def test_location_delete(self):
        """Deleting a location removes it from the database."""
        location = Location.objects.create(
            country="US",
            region="New York",
            city="New York",
            postal_code="10001"
        )
        pk = location.pk
        location.delete()
        self.assertFalse(Location.objects.filter(pk=pk).exists())






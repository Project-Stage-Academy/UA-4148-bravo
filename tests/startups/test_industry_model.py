from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from startups.models import Industry
from tests.test_base_case import BaseAPITestCase
from tests.test_disable_signal_mixin import DisableSignalMixin


class IndustryModelCleanTests(DisableSignalMixin, BaseAPITestCase):
    """Test suite for Industry model validation and constraints."""

    def test_create_industry_success(self):
        """Industry can be created successfully with valid data."""
        industry = Industry.objects.create(name="Information Technology")
        self.assertEqual(industry.name, "Information Technology")
        self.assertTrue(industry.pk is not None)

    def test_create_industry_duplicate_name_raises_error(self):
        """Creating industry with duplicate name raises IntegrityError."""
        Industry.objects.create(name="FinTech")
        with self.assertRaises(DjangoValidationError):
            industry = Industry(name="FinTech")
            industry.full_clean()
            industry.save()

    def test_industry_name_not_empty(self):
        """Industry name cannot be empty."""
        with self.assertRaises(DjangoValidationError):
            industry = Industry(name="")
            industry.full_clean()
            industry.save()

    def test_industry_str_method(self):
        """__str__ method returns the industry name."""
        industry = Industry.objects.create(name="HealthTech")
        self.assertEqual(str(industry), "HealthTech")

    def test_industry_update_name(self):
        """Updating industry name works correctly."""
        industry = Industry.objects.create(name="OldName")
        industry.name = "NewName"
        industry.full_clean()
        industry.save()
        self.assertEqual(Industry.objects.get(pk=industry.pk).name, "NewName")

    def test_industry_delete(self):
        """Deleting an industry removes it from the database."""
        industry = Industry.objects.create(name="ToDelete")
        pk = industry.pk
        industry.delete()
        self.assertFalse(Industry.objects.filter(pk=pk).exists())



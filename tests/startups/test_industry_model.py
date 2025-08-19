from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from django.db import IntegrityError
from startups.models import Industry
from tests.test_base_case import BaseAPITestCase
from unittest.mock import patch
from startups.documents import StartupDocument


class IndustryModelCleanTests(BaseAPITestCase):
    """Test suite for Industry model validation and constraints."""

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

    def test_create_industry_success(self):
        """Industry can be created successfully with valid data."""
        industry = Industry.objects.create(name="Information Technology")
        self.assertEqual(industry.name, "Information Technology")
        self.assertTrue(industry.pk is not None)

    def test_create_industry_duplicate_name_raises_error(self):
        """Creating industry with duplicate name raises IntegrityError or ValidationError."""
        Industry.objects.create(name="FinTech")
        with self.assertRaises((DjangoValidationError, IntegrityError)):
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




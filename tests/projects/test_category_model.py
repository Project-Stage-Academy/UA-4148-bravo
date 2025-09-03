from django.test import TestCase
from unittest.mock import patch

from projects.models import Category


class CategoryModelTests(TestCase):
    """Tests for the Category model."""

    def test_create_category(self):
        """Category can be created with valid data."""
        category = Category.objects.create(name="Tech", description="Technology related projects")
        self.assertEqual(category.name, "Tech")
        self.assertEqual(category.description, "Technology related projects")
        self.assertIsNotNone(category.created_at)

    def test_name_must_be_unique(self):
        """Category name must be unique."""
        Category.objects.create(name="Health")
        with self.assertRaises(Exception):
            Category.objects.create(name="Health")  # Duplicate name

    def test_str_returns_name(self):
        """__str__ method should return the category name."""
        category = Category.objects.create(name="Finance")
        self.assertEqual(str(category), "Finance")

    def test_ordering_by_name(self):
        """Categories should be ordered alphabetically by name."""
        cat_b = Category.objects.create(name="Beta")
        cat_a = Category.objects.create(name="Alpha")
        categories = list(Category.objects.all())
        self.assertEqual(categories, [cat_a, cat_b])

    @patch("projects.models.validate_forbidden_names")
    def test_clean_calls_validate_forbidden_names(self, mock_validate):
        """clean() should call validate_forbidden_names with correct arguments."""
        category = Category(name="TestName")
        category.clean()
        mock_validate.assert_called_once_with("TestName", field_name="name")

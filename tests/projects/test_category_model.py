from django.test import TestCase
from django.db import IntegrityError
from unittest.mock import patch
from projects.models import Category
import uuid


class CategoryModelTests(TestCase):
    """Tests for the Category model."""

    def test_create_category(self):
        """Category can be created with valid data."""
        unique_id = uuid.uuid4().hex[:8]
        category = Category.objects.create(name=f"Tech_{unique_id}", description="Technology related projects")
        self.assertEqual(category.name, f"Tech_{unique_id}")
        self.assertEqual(category.description, "Technology related projects")
        self.assertIsNotNone(category.created_at)

    def test_name_must_be_unique(self):
        """Category name must be unique."""
        unique_id = uuid.uuid4().hex[:8]
        Category.objects.create(name=f"Health_{unique_id}")
        with self.assertRaises(IntegrityError):
            Category.objects.create(name=f"Health_{unique_id}") 

    def test_str_returns_name(self):
        """__str__ method should return the category name."""
        unique_id = uuid.uuid4().hex[:8]
        category = Category.objects.create(name=f"Finance_{unique_id}")
        self.assertEqual(str(category), f"Finance_{unique_id}")

    def test_ordering_by_name(self):
        """Categories should be ordered alphabetically by name."""
        unique_id = uuid.uuid4().hex[:8]
        cat_b = Category.objects.create(name=f"Beta_{unique_id}")
        cat_a = Category.objects.create(name=f"Alpha_{unique_id}")
        categories = list(Category.objects.all())
        self.assertEqual(categories, [cat_a, cat_b])

    @patch("projects.models.validate_forbidden_names")
    def test_clean_calls_validate_forbidden_names(self, mock_validate):
        """clean() should call validate_forbidden_names with correct arguments."""
        unique_id = uuid.uuid4().hex[:8]
        category = Category(name=f"TestName_{unique_id}")
        category.clean()
        mock_validate.assert_called_once_with(f"TestName_{unique_id}", field_name="name")

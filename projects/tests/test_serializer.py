from django.core.files.uploadedfile import SimpleUploadedFile
from projects.serializers import ProjectWriteSerializer
from tests.test_setup import BaseProjectTestCase
import ddt
from django.db import IntegrityError


class ProjectSerializerBaseTests(BaseProjectTestCase):
    """
    Test suite for validating ProjectSerializer behavior, including
    required fields, file uploads, and validation constraints.
    """

    def test_participant_without_goal_should_fail(self):
        """
        Validate that a project marked as participant must have a funding_goal.
        Expect serializer validation to fail if funding_goal is missing.
        """
        data = {
            'startup': self.startup.id,
            'title': 'Participant',
            'is_participant': True,
            'current_funding': '1000.00',
            'category': self.category.id,
            'email': 'participant@example.com'
        }
        serializer = ProjectWriteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('funding_goal', serializer.errors)

    def test_valid_project_data(self):
        """
        Validate that a project with all required fields and a valid business plan
        file uploads correctly and passes serializer validation.
        """
        plan_file = SimpleUploadedFile(
            "plan.pdf",
            b"%PDF-1.4 Dummy PDF content here",
            content_type="application/pdf"
        )
        data = {
            "title": "Unique Test Project",
            "email": "test@example.com",
            "funding_goal": 10000,
            "current_funding": 5000,
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "business_plan": plan_file,
            "social_links": ["https://example.com"]
        }
        serializer = ProjectWriteSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_current_funding_exceeds_goal_should_fail(self):
        """
        Validate that the serializer rejects a project where current_funding
        exceeds the funding_goal.
        """
        plan_file = SimpleUploadedFile(
            "plan.pdf",
            b"%PDF-1.4 Dummy PDF content here",
            content_type="application/pdf"
        )
        data = {
            "title": "Project X",
            "email": "x@example.com",
            "funding_goal": 1000,
            "current_funding": 2000,
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "business_plan": plan_file,
            "social_links": []
        }
        serializer = ProjectWriteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("current_funding", serializer.errors)

    def test_missing_business_plan_for_completed_should_fail(self):
        """
        Validate that a project which has completed funding (current_funding == funding_goal)
        must provide a business_plan file; serializer should fail otherwise.
        """
        data = {
            "title": "Project Y",
            "email": "y@example.com",
            "funding_goal": 5000,
            "current_funding": 5000,
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "social_links": []
        }
        serializer = ProjectWriteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("business_plan", serializer.errors)

    def test_duplicate_title_should_fail(self):
        """
        If Project title must be unique, test creating a project with
        a duplicate title fails validation or raises integrity error.
        """
        self.create_project(
            title="Unique Project",
            email="existing@example.com",
            funding_goal=1000,
            current_funding=0,
            startup=self.startup,
            category=self.category,
        )
        data = {
            "title": "Unique Project",  # duplicate title
            "email": "new@example.com",
            "funding_goal": 5000,
            "current_funding": 0,
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "social_links": []
        }
        serializer = ProjectWriteSerializer(data=data)
        if serializer.is_valid():
            with self.assertRaises(IntegrityError):
                serializer.save()
        else:
            self.assertIn('title', serializer.errors)

    def test_update_funding_goal_less_than_current_should_fail(self):
        """
        Test that updating the funding_goal to a value less than the current_funding
        causes serializer validation to fail with an error on 'current_funding'.
        """
        project = self.create_project(
            title="Test Project",
            email="testupdate@example.com",
            funding_goal=1000,
            current_funding=800,
            startup=self.startup,
            category=self.category,
        )
        data = {
            "funding_goal": "500.00",
        }
        serializer = ProjectWriteSerializer(instance=project, data=data, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('current_funding', serializer.errors)


@ddt.ddt
class ProjectSerializerValidationTests(BaseProjectTestCase):

    @ddt.data(
        'title',
        'email',
        'funding_goal',
        'startup_id',
        'category_id',
    )
    def test_missing_required_fields_should_fail(self, missing_field):
        """
        Test that omitting each required field individually
        results in a validation error for that specific missing field.
        """
        data = {
            "title": "Test Missing Fields",
            "email": "testmissing@example.com",
            "funding_goal": 1000,
            "current_funding": 0,
            "startup_id": self.startup.id,
            "category_id": self.category.id,
        }
        data.pop(missing_field)
        serializer = ProjectWriteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn(missing_field, serializer.errors)

    @ddt.data(
        {"title": 12345},
        {"email": 67890},
        {"funding_goal": "not_a_number"},
        {"current_funding": "also_not_a_number"},
        {"startup_id": "invalid_id"},
        {"category_id": "invalid_id"},
        {"social_links": "not_a_list"},
    )
    @ddt.unpack
    def test_invalid_field_types_should_fail(self, **invalid_field):
        """
        Test that providing invalid data types for fields
        causes serializer validation errors for those fields.
        """
        valid_data = {
            "title": "Valid Title",
            "email": "valid@example.com",
            "funding_goal": 1000,
            "current_funding": 0,
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "social_links": [],
        }

        valid_data.update(invalid_field)
        serializer = ProjectWriteSerializer(data=valid_data)
        self.assertFalse(serializer.is_valid())

        error_field = list(invalid_field.keys())[0]
        self.assertIn(error_field, serializer.errors)

    @ddt.data(
        ("0.00", True),
        ("-0.01", False),
        ("9999999999999999999999.99", True),
        ("10000000000000000000000.00", False),
    )
    @ddt.unpack
    def test_funding_goal_edge_cases(self, funding_goal_value, should_be_valid):
        """
        Test funding_goal with edge numeric values:
        - zero value should pass validation,
        - negative values should fail,
        - extremely large but valid values should pass,
        - values exceeding max_digits should fail.
        """
        data = {
            "title": "Funding Edge Case",
            "email": "edgecase@example.com",
            "funding_goal": funding_goal_value,
            "current_funding": "0.00",
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "business_plan": SimpleUploadedFile("plan.pdf", b"dummy", content_type="application/pdf"),
            "social_links": [],
        }
        serializer = ProjectWriteSerializer(data=data)
        self.assertEqual(serializer.is_valid(), should_be_valid)
        if not should_be_valid:
            self.assertIn('funding_goal', serializer.errors)

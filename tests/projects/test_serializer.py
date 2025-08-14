import ddt
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from projects.serializers import ProjectWriteSerializer
from tests.test_base_case import BaseAPITestCase


class ProjectSerializerBaseTests(BaseAPITestCase):

    def get_dummy_file(self):
        """Return a valid dummy PDF file for testing file uploads."""
        return SimpleUploadedFile(
            "plan.pdf",
            b"%PDF-1.4 Dummy PDF content",
            content_type="application/pdf"
        )

    def test_participant_without_goal_should_fail(self):
        """Participant project without funding_goal should fail validation."""
        data = {
            'startup_id': self.startup.id,
            'title': 'Participant',
            'is_participant': True,
            'current_funding': '1000.00',
            'category_id': self.category.id,
            'email': 'participant@example.com',
            'funding_goal': None
        }
        serializer = ProjectWriteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('funding_goal', serializer.errors)

    def test_valid_project_data(self):
        """Project with all required fields and valid business_plan passes validation."""
        data = {
            "title": "Valid Project",
            "email": "valid@example.com",
            "funding_goal": "10000.00",
            "current_funding": "5000.00",
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "business_plan": self.get_dummy_file(),
        }
        serializer = ProjectWriteSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_current_funding_exceeds_goal_should_fail(self):
        """Serializer rejects current_funding exceeding funding_goal."""
        data = {
            "title": "OverFunded",
            "email": "overfunded@example.com",
            "funding_goal": "1000.00",
            "current_funding": "2000.00",
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "business_plan": self.get_dummy_file(),
        }
        serializer = ProjectWriteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("current_funding", serializer.errors)

    def test_missing_business_plan_for_completed_should_fail(self):
        """Project with funding_goal == current_funding must have business_plan."""
        data = {
            "title": "CompletedProject",
            "email": "completed@example.com",
            "funding_goal": "5000.00",
            "current_funding": "5000.00",
            "startup_id": self.startup.id,
            "category_id": self.category.id,
        }
        serializer = ProjectWriteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("business_plan", serializer.errors)

    def test_duplicate_title_should_fail(self):
        """Creating a project with duplicate title under same startup fails."""
        self.get_or_create_project(
            title="Unique Project",
            email="existing@example.com",
            funding_goal=1000,
            current_funding=0,
            startup=self.startup,
            category=self.category,
        )
        data = {
            "title": "Unique Project",
            "email": "new@example.com",
            "funding_goal": "5000.00",
            "current_funding": "0.00",
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "business_plan": self.get_dummy_file(),
        }
        serializer = ProjectWriteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertTrue(
            any("title" in str(e) for e in serializer.errors["non_field_errors"])
        )

    def test_update_funding_goal_less_than_current_should_fail(self):
        """Updating funding_goal < current_funding should fail validation."""
        project = self.get_or_create_project(
            title="Test Update Project",
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
class ProjectSerializerValidationTests(BaseAPITestCase):

    def get_dummy_file(self):
        return SimpleUploadedFile(
            "plan.pdf",
            b"%PDF-1.4 Dummy PDF content",
            content_type="application/pdf"
        )

    @ddt.data(
        'title',
        'email',
        'funding_goal',
        'startup_id',
        'category_id',
    )
    def test_missing_required_fields_should_fail(self, missing_field):
        """Omitting required fields individually triggers validation errors."""
        data = {
            "title": "Test Missing",
            "email": "testmissing@example.com",
            "funding_goal": Decimal("1000.00"),
            "current_funding": Decimal("0.00"),
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "business_plan": self.get_dummy_file(),
        }
        data.pop(missing_field)
        serializer = ProjectWriteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn(missing_field, serializer.errors)

    @ddt.data(
        {"title": []},
        {"email": []},
        {"funding_goal": "not_a_number"},
        {"current_funding": "also_not_a_number"},
        {"startup_id": "invalid_id"},
        {"category_id": "invalid_id"},
    )
    @ddt.unpack
    def test_invalid_field_types_should_fail(self, **invalid_field):
        valid_data = {
            "title": "Valid Title",
            "email": "valid@example.com",
            "funding_goal": Decimal("1000.00"),
            "current_funding": Decimal("0.00"),
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "business_plan": self.get_dummy_file(),
        }
        valid_data.update(invalid_field)
        serializer = ProjectWriteSerializer(data=valid_data)
        self.assertFalse(serializer.is_valid())
        error_field = list(invalid_field.keys())[0]
        self.assertTrue(
            error_field in serializer.errors or "non_field_errors" in serializer.errors
        )

    @ddt.data(
        ("0.01", True),
        ("0.00", False),
        ("-0.01", False),
        ("999999999999999999.99", True),
        ("10000000000000000000000.00", False),
    )
    @ddt.unpack
    def test_funding_goal_edge_cases(self, funding_goal_value, should_be_valid):
        data = {
            "title": "Funding Edge",
            "email": "edge@example.com",
            "funding_goal": Decimal(funding_goal_value),
            "current_funding": Decimal("0.00"),
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "business_plan": self.get_dummy_file(),
        }
        serializer = ProjectWriteSerializer(data=data)
        self.assertEqual(serializer.is_valid(), should_be_valid)
        if not should_be_valid:
            self.assertTrue(
                'funding_goal' in serializer.errors or 'current_funding' in serializer.errors
            )

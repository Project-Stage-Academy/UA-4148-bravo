from projects.serializers import ProjectSerializer
from django.core.files.uploadedfile import SimpleUploadedFile
from tests.test_setup import BaseProjectTestCase


class ProjectSerializerTests(BaseProjectTestCase):

    def test_participant_without_goal_should_fail(self):
        data = {
            'startup': self.startup.id,
            'title': 'Participant',
            'is_participant': True,
            'current_funding': '1000.00',
            'category': self.category.id,
            'email': 'participant@example.com'
        }
        serializer = ProjectSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('funding_goal', serializer.errors)

    def test_valid_project_data(self):
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
        serializer = ProjectSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_current_funding_exceeds_goal_should_fail(self):
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
        serializer = ProjectSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("current_funding", serializer.errors)

    def test_missing_business_plan_for_completed_should_fail(self):
        data = {
            "title": "Project Y",
            "email": "y@example.com",
            "funding_goal": 5000,
            "current_funding": 5000,
            "startup_id": self.startup.id,
            "category_id": self.category.id,
            "social_links": []
        }
        serializer = ProjectSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("business_plan", serializer.errors)

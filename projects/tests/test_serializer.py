from django.contrib.auth import get_user_model
from django.test import TestCase

from projects.models import Category
from projects.serializers import ProjectSerializer
from startups.models import Startup

User = get_user_model()


class ProjectSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='founder')
        self.startup = Startup.objects.create(user=self.user, company_name='TestStartup')
        self.category = Category.objects.create(name='Tech')

    def test_valid_project_data(self):
        data = {
            'startup': self.startup.id,
            'title': 'AI Platform',
            'description': 'Smart analytics',
            'status': 'draft',
            'duration': 30,
            'funding_goal': '100000.00',
            'current_funding': '5000.00',
            'category': self.category.id,
            'email': 'project@example.com',
            'has_patents': True,
            'is_participant': False,
            'is_active': True
        }
        serializer = ProjectSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_current_funding_exceeds_goal_should_fail(self):
        data = {
            'startup': self.startup.id,
            'title': 'Overfunded',
            'funding_goal': '10000.00',
            'current_funding': '20000.00',
            'category': self.category.id,
            'email': 'over@example.com'
        }
        serializer = ProjectSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('current_funding', serializer.errors)

    def test_missing_business_plan_for_completed_should_fail(self):
        data = {
            'startup': self.startup.id,
            'title': 'NoPlan',
            'status': 'completed',
            'funding_goal': '50000.00',
            'current_funding': '10000.00',
            'category': self.category.id,
            'email': 'noplan@example.com'
        }
        serializer = ProjectSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('business_plan', serializer.errors)

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

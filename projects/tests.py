from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from django.contrib.auth import get_user_model
from profiles.models import Startup, Industry
from projects.models import Project, Category
from projects.serializers import ProjectSerializer

User = get_user_model()


# ─────────────────────────────────────────────────────────────
# SERIALIZER TESTS
# ─────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────
# MODEL CLEAN() TESTS
# ─────────────────────────────────────────────────────────────

class ProjectModelCleanTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='modeluser')
        self.startup = Startup.objects.create(user=self.user, company_name='CleanStartup')
        self.category = Category.objects.create(name='CleanTech')

    def test_clean_should_raise_for_invalid_funding(self):
        project = Project(
            startup=self.startup,
            title='BadFunding',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('20000.00'),
            category=self.category,
            email='bad@example.com'
        )
        with self.assertRaises(ValidationError) as context:
            project.clean()
        self.assertIn('current_funding', context.exception.message_dict)

    def test_clean_should_raise_for_missing_plan(self):
        project = Project(
            startup=self.startup,
            title='MissingPlan',
            status='completed',
            funding_goal=Decimal('50000.00'),
            current_funding=Decimal('10000.00'),
            category=self.category,
            email='missing@example.com'
        )
        with self.assertRaises(ValidationError) as context:
            project.clean()
        self.assertIn('business_plan', context.exception.message_dict)


# ─────────────────────────────────────────────────────────────
# API TESTS
# ─────────────────────────────────────────────────────────────

class ProjectAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='pass')
        self.startup = Startup.objects.create(user=self.user, company_name='APIStartup')
        self.category = Category.objects.create(name='API Tech')
        self.client.login(username='apiuser', password='pass')

    def test_create_project(self):
        url = reverse('project-list')
        data = {
            'startup': self.startup.id,
            'title': 'API Project',
            'funding_goal': '50000.00',
            'current_funding': '1000.00',
            'category': self.category.id,
            'email': 'api@example.com'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'API Project')

    def test_get_project_list(self):
        Project.objects.create(
            startup=self.startup,
            title='ListProject',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email='list@example.com'
        )
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_update_project(self):
        project = Project.objects.create(
            startup=self.startup,
            title='UpdateMe',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email='update@example.com'
        )
        url = reverse('project-detail', args=[project.id])
        data = {'title': 'UpdatedTitle'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'UpdatedTitle')

    def test_delete_project(self):
        project = Project.objects.create(
            startup=self.startup,
            title='DeleteMe',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email='delete@example.com'
        )
        url = reverse('project-detail', args=[project.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from projects.models import Project, Category
from startups.models import Startup, Industry, Location

from rest_framework.test import APIClient

from users.models import UserRole, User


class ProjectAPITests(APITestCase):
    def setUp(self):
        role = UserRole.objects.get(role='user')
        self.user = User.objects.create_user(
            email='apiinvestor@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Investor',
            role=role,
        )
        self.user.refresh_from_db()

        self.industry = Industry.objects.create(name="Technology")
        self.location = Location.objects.create(country="US")

        self.startup = Startup.objects.create(
            user=self.user,
            company_name='ListStartup',
            founded_year=2019,
            industry=self.industry,
            location=self.location
        )
        self.category = Category.objects.create(name='API Tech')

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

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

    # ─────────────────────────────────────────────────────────
    # NEGATIVE PERMISSION TESTS
    # ─────────────────────────────────────────────────────────

    def test_unauthenticated_user_cannot_create_project(self):
        self.client.logout()
        url = reverse('project-list')
        data = {
            'startup': self.startup.id,
            'title': 'Unauthorized',
            'funding_goal': '10000.00',
            'current_funding': '500.00',
            'category': self.category.id,
            'email': 'unauth@example.com'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_access_project_list(self):
        self.client.logout()
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_update_other_users_project(self):
        other_user = User.objects.create_user(username='otheruser', password='pass')
        other_startup = Startup.objects.create(user=other_user, company_name='OtherStartup')
        project = Project.objects.create(
            startup=other_startup,
            title='OtherProject',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email='other@example.com'
        )
        url = reverse('project-detail', args=[project.id])
        data = {'title': 'HackedTitle'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_delete_other_users_project(self):
        other_user = User.objects.create_user(username='otheruser2', password='pass')
        other_startup = Startup.objects.create(user=other_user, company_name='OtherStartup2')
        project = Project.objects.create(
            startup=other_startup,
            title='OtherDelete',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email='otherdelete@example.com'
        )
        url = reverse('project-detail', args=[project.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from tests.test_setup import BaseProjectTestCase


class ProjectAPITests(BaseProjectTestCase):

    def get_project_data(self, **overrides):
        data = {
            'startup_id': self.startup.id,
            'title': 'Default Project',
            'funding_goal': '50000.00',
            'current_funding': '1000.00',
            'category_id': self.category.id,
            'email': 'default@example.com',
        }
        data.update(overrides)
        return data

    def create_other_user_startup_project(self, project_title, project_email):
        other_user = self.create_user(
            email='apiother@example.com',
            first_name='Api',
            last_name='Other'
        )
        other_startup = self.create_startup(
            user=other_user,
            company_name='ListStartup',
            founded_year=2019,
            industry=self.industry,
            location=self.location
        )
        project = self.create_project(
            startup=other_startup,
            title=project_title,
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email=project_email
        )
        return project

    def test_create_project(self):
        url = reverse('project-list')
        data = self.get_project_data(title='API Project', email='api@example.com')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], data['title'])

    def test_get_project_list(self):
        self.create_project(
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
        project = self.create_project(
            startup=self.startup,
            title='UpdateMe',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email='update@example.com'
        )
        url = reverse('project-detail', args=[project.pk])
        data = {'title': 'UpdatedTitle'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], data['title'])

    def test_delete_project(self):
        project = self.create_project(
            startup=self.startup,
            title='DeleteMe',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email='delete@example.com'
        )
        url = reverse('project-detail', args=[project.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ─────────────────────────────────────────────────────────
    # NEGATIVE PERMISSION TESTS
    # ─────────────────────────────────────────────────────────

    def test_unauthenticated_user_cannot_create_project(self):
        self.client.logout()
        url = reverse('project-list')
        data = self.get_project_data(
            title='Unauthorized',
            email='unauth@example.com'
        )
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_access_project_list(self):
        self.client.logout()
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_update_other_users_project(self):
        project = self.create_other_user_startup_project('OtherProject', 'other@example.com')
        url = reverse('project-detail', args=[project.pk])
        data = {'title': 'HackedTitle'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_delete_other_users_project(self):
        project = self.create_other_user_startup_project('OtherDelete', 'otherdelete@example.com')
        url = reverse('project-detail', args=[project.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

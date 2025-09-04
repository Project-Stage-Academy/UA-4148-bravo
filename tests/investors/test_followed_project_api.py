from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.db import connection

from investors.models import Investor, FollowedProject
from projects.models import Project
from startups.models import Startup
from communications.models import NotificationType
from common.models import Industry, Location, Category
from common.enums import Stage

User = get_user_model()

class FollowedProjectAPITests(TestCase):
    reset_sequences = True

    def setUp(self):
        self.industry = Industry.objects.create(name="IT")
        self.location = Location.objects.create(
            country="US", region="CA", city="SF", postal_code="94105"
        )
        self.category = Category.objects.create(name="Technology")

        # Create investor user and profile
        self.investor_user = User.objects.create_user(
            email="investor@example.com", password="Pass123!", first_name="Ivan"
        )
        self.investor = Investor.objects.create(
            user=self.investor_user,
            company_name="API Capital",
            industry=self.industry,
            location=self.location,
            founded_year=2020,
            stage=Stage.MVP,
            fund_size="1000000.00",
        )

        # Create startup user and profile
        self.startup_user = User.objects.create_user(
            email="owner@example.com", password="Pass123!", first_name="Owner"
        )
        self.startup = Startup.objects.create(
            user=self.startup_user,
            company_name="Rocket",
            industry=self.industry,
            location=self.location,
            founded_year=2021,
            stage=Stage.MVP,
            email="rocket@example.com",
        )

        # Create a project for the startup
        self.project = Project.objects.create(
            startup=self.startup,
            title="AI-Powered Analytics Platform",
            description="Revolutionary analytics platform using AI",
            category=self.category,
            funding_goal="500000.00",
            email="project@rocket.com"
        )

        self.client = APIClient()
        Notification.objects.all().delete()

    def _authenticate_as_investor(self):
        """Helper method to authenticate as investor user."""
        self.client.force_authenticate(user=self.investor_user)

    def _authenticate_as_startup(self):
        """Helper method to authenticate as startup user."""
        self.client.force_authenticate(user=self.startup_user)

    def test_follow_project_via_api_creates_notification(self):
        """Test that following a project via API creates a notification."""
        self._authenticate_as_investor()
        
        url = f'/api/v1/projects/follow/{self.project.id}/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FollowedProject.objects.count(), 1)
        
        try:
            connection.commit()
        except Exception:
            pass

        # Check notification was created
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.user, self.startup_user)
        self.assertEqual(notif.related_project, self.project)

    def test_follow_project_twice_returns_200(self):
        """Test that following the same project twice returns 200 (already followed)."""
        self._authenticate_as_investor()
        
        url = f'/api/v1/projects/follow/{self.project.id}/'
        
        # First follow
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Second follow (should return 200)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should still only have one FollowedProject
        self.assertEqual(FollowedProject.objects.count(), 1)

    def test_follow_nonexistent_project_returns_404(self):
        """Test that following a non-existent project returns 404."""
        self._authenticate_as_investor()
        
        url = '/api/v1/projects/follow/99999/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_follow_returns_401(self):
        """Test that unauthenticated users cannot follow projects."""
        url = f'/api/v1/projects/follow/{self.project.id}/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_investor_cannot_follow_project(self):
        """Test that non-investor users cannot follow projects."""
        # Create a regular user without investor profile
        regular_user = User.objects.create_user(
            email="regular@example.com", password="Pass123!"
        )
        self.client.force_authenticate(user=regular_user)
        
        url = f'/api/v1/projects/follow/{self.project.id}/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_followed_project_viewset_list(self):
        """Test listing followed projects via ViewSet."""
        self._authenticate_as_investor()
        
        # Create a followed project
        FollowedProject.objects.create(investor=self.investor, project=self.project)
        
        url = '/api/v1/investors/followed-projects/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['project'], self.project.id)

    def test_followed_project_viewset_create(self):
        """Test creating followed project via ViewSet."""
        self._authenticate_as_investor()
        
        url = '/api/v1/investors/followed-projects/'
        data = {
            'project': self.project.id,
            'status': 'interested',
            'notes': 'This looks promising'
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FollowedProject.objects.count(), 1)
        
        followed = FollowedProject.objects.first()
        self.assertEqual(followed.status, 'interested')
        self.assertEqual(followed.notes, 'This looks promising')

    def test_followed_project_viewset_update(self):
        """Test updating followed project via ViewSet."""
        self._authenticate_as_investor()
        
        followed = FollowedProject.objects.create(
            investor=self.investor, 
            project=self.project,
            status='watching'
        )
        
        url = f'/api/v1/investors/followed-projects/{followed.id}/'
        data = {
            'status': 'contacted',
            'notes': 'Reached out to the team'
        }
        response = self.client.patch(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        followed.refresh_from_db()
        self.assertEqual(followed.status, 'contacted')
        self.assertEqual(followed.notes, 'Reached out to the team')

    def test_followed_project_viewset_delete(self):
        """Test deleting followed project via ViewSet."""
        self._authenticate_as_investor()
        
        followed = FollowedProject.objects.create(
            investor=self.investor, 
            project=self.project
        )
        
        url = f'/api/v1/investors/followed-projects/{followed.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(FollowedProject.objects.count(), 0)

    def test_investor_cannot_access_other_investor_followed_projects(self):
        """Test that investors can only access their own followed projects."""
        # Create second investor
        investor2_user = User.objects.create_user(
            email="investor2@example.com", password="Pass123!"
        )
        investor2 = Investor.objects.create(
            user=investor2_user,
            company_name="Beta Ventures",
            industry=self.industry,
            location=self.location,
            founded_year=2019,
            stage=Stage.SCALE,
            fund_size="2000000.00",
        )
        
        # Create followed project for first investor
        followed = FollowedProject.objects.create(
            investor=self.investor, 
            project=self.project
        )
        
        # Authenticate as second investor
        self.client.force_authenticate(user=investor2_user)
        
        # Try to access first investor's followed project
        url = f'/api/v1/investors/followed-projects/{followed.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_follow_own_project_validation(self):
        """Test that users cannot follow their own projects."""
        # Create investor who is also a startup owner
        mixed_user = User.objects.create_user(
            email="mixed@example.com", password="Pass123!"
        )
        mixed_investor = Investor.objects.create(
            user=mixed_user,
            company_name="Mixed Company",
            industry=self.industry,
            location=self.location,
            founded_year=2020,
            stage=Stage.MVP,
            fund_size="500000.00",
        )
        mixed_startup = Startup.objects.create(
            user=mixed_user,  # Same user
            company_name="Mixed Startup",
            industry=self.industry,
            location=self.location,
            founded_year=2021,
            stage=Stage.MVP,
            email="mixed@startup.com",
        )
        mixed_project = Project.objects.create(
            startup=mixed_startup,
            title="Own Project",
            description="Project owned by the investor",
            category=self.category,
            funding_goal="100000.00",
            email="own@project.com"
        )
        
        self.client.force_authenticate(user=mixed_user)
        
        url = f'/api/v1/projects/follow/{mixed_project.id}/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('own project', str(response.data).lower())

    def test_api_response_includes_project_details(self):
        """Test that API response includes relevant project details."""
        self._authenticate_as_investor()
        
        url = f'/api/v1/projects/follow/{self.project.id}/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        data = response.data
        self.assertEqual(data['project'], self.project.id)
        self.assertEqual(data['project_title'], self.project.title)
        self.assertEqual(data['startup_name'], self.startup.company_name)
        self.assertEqual(data['status'], 'watching')  # default status

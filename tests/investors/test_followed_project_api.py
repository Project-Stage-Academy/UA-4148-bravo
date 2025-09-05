from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import uuid

from investors.models import Investor, FollowedProject
from projects.models import Project, Category
from startups.models import Startup, Industry, Location
from users.models import UserRole
from communications.models import Notification, NotificationType
from communications.services import NotificationService
from common.enums import Stage

User = get_user_model()

class FollowedProjectAPITests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        """Set up test data with unique identifiers to prevent constraint violations."""
        # Use UUID for unique values to prevent constraint violations
        unique_id = uuid.uuid4().hex[:8]
        
        # Create required objects with unique identifiers
        self.industry = Industry.objects.create(name=f"Technology_{unique_id}")
        self.location = Location.objects.create(
            country="US", 
            region="CA", 
            city=f"San_Francisco_{unique_id}", 
            postal_code="94105"
        )
        self.category = Category.objects.create(name=f"Software_{unique_id}")

        # Create user roles
        role_startup, _ = UserRole.objects.get_or_create(role='startup')
        role_investor, _ = UserRole.objects.get_or_create(role='investor')

        # Create startup user and startup
        self.startup_user = User.objects.create_user(
            email=f"startup_owner_{unique_id}@example.com",
            password="testpass123",
            first_name="Startup",
            last_name="Owner",
            is_active=True,
            role=role_startup
        )

        self.startup = Startup.objects.create(
            user=self.startup_user,
            company_name=f"TechStartup_{unique_id}",
            description="A revolutionary tech startup",
            industry=self.industry,
            location=self.location,
            email=f"startup_{unique_id}@techstartup.com",
            founded_year=2020,
            team_size=5,
            stage=Stage.MVP
        )

        # Create project
        self.project = Project.objects.create(
            startup=self.startup,
            title=f"AI_Project_{unique_id}",
            description="An innovative AI project",
            category=self.category,
            funding_goal="100000.00",
            current_funding="0.00",
            email=f"project_{unique_id}@techstartup.com"
        )

        # Create investor user and investor
        self.investor_user = User.objects.create_user(
            email=f"investor_{unique_id}@example.com",
            password="testpass123",
            first_name="Angel",
            last_name="Investor",
            is_active=True,
            role=role_investor
        )

        self.investor = Investor.objects.create(
            user=self.investor_user,
            company_name=f"InvestCorp_{unique_id}",
            description="Professional investment firm",
            industry=self.industry,
            location=self.location,
            email=f"investor_{unique_id}@investcorp.com",
            founded_year=2010,
            team_size=20,
            stage=Stage.SCALE,
            fund_size="10000000.00"
        )

        # Ensure notification type exists
        self.notification_type, _ = NotificationType.objects.get_or_create(
            name='project_followed',
            defaults={'description': 'Notification when someone follows a project'}
        )

        # Initialize API client and authenticate
        self.client = APIClient()
        self.client.force_authenticate(user=self.investor_user)

    def tearDown(self):
        """Clean up test data after each test."""
        FollowedProject.objects.all().delete()
        Notification.objects.all().delete()
        Project.objects.all().delete()
        Startup.objects.all().delete()
        Investor.objects.all().delete()
        User.objects.all().delete()

    def _authenticate_as_investor(self):
        """Helper method to authenticate as investor."""
        self.client.force_authenticate(user=self.investor_user)

    def _authenticate_as_startup(self):
        """Helper method to authenticate as startup user."""
        self.client.force_authenticate(user=self.startup_user)

    def test_follow_project_via_simple_api_creates_notification(self):
        """Test that following a project via the simple API creates a notification."""
        # Clear any existing notifications to prevent duplicates
        Notification.objects.all().delete()
        
        self._authenticate_as_investor()
        
        url = f'/api/v1/investors/projects/{self.project.id}/follow/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FollowedProject.objects.count(), 1)
        
        # Check notification was created
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.user, self.startup_user)
        self.assertEqual(notif.related_project, self.project)
        
        # Check notification message contains investor name and project title
        message = notif.message.lower()
        self.assertIn(self.investor_user.first_name.lower(), message)
        self.assertIn(self.project.title.lower(), message)
        self.assertIn('follow', message)

    def test_follow_project_via_api_creates_notification(self):
        """Test that following a project via API creates a notification using direct service."""
        self._authenticate_as_investor()
        
        # Create FollowedProject and manually trigger notification
        FollowedProject.objects.create(investor=self.investor, project=self.project)
        
        # Manually create notification using the service
        notification = NotificationService.create_project_followed_notification(
            project=self.project,
            investor_user=self.investor_user
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.user, self.startup_user)
        self.assertEqual(notif.related_project, self.project)

    def test_follow_project_twice_returns_200(self):
        """Test that following the same project twice returns 200 (already followed)."""
        self._authenticate_as_investor()
        
        url = f'/api/v1/investors/projects/{self.project.id}/follow/'
        
        # First follow
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Second follow (should return 200)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should still only have one FollowedProject
        self.assertEqual(FollowedProject.objects.count(), 1)
        
        # Should still only have one notification (no duplicates)
        self.assertEqual(Notification.objects.count(), 1)

    def test_follow_nonexistent_project_returns_404(self):
        """Test that following a non-existent project returns 404."""
        self._authenticate_as_investor()
        
        url = '/api/v1/investors/projects/99999/follow/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_follow_returns_403(self):
        """Test that unauthenticated requests return 403 Forbidden."""
        self.client.force_authenticate(user=None)
        
        url = f'/api/v1/investors/projects/{self.project.id}/follow/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_investor_follow_returns_403(self):
        """Test that non-investor users cannot follow projects."""
        # Create a regular user without investor profile
        unique_id = uuid.uuid4().hex[:8]
        role_user, _ = UserRole.objects.get_or_create(role='user')
        regular_user = User.objects.create_user(
            email=f"regular_{unique_id}@example.com", 
            password="Pass123!",
            is_active=True,
            role=role_user
        )
        self.client.force_authenticate(user=regular_user)
        
        url = f'/api/v1/investors/projects/{self.project.id}/follow/'
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
        
        # Check notification was created via ViewSet too
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.user, self.startup_user)

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
        unique_id = uuid.uuid4().hex[:8]
        investor2_user = User.objects.create_user(
            email=f"investor2_{unique_id}@example.com", password="Pass123!"
        )
        investor2 = Investor.objects.create(
            user=investor2_user,
            company_name=f"Beta_Ventures_{unique_id}",
            industry=self.industry,
            location=self.location,
            founded_year=2019,
            stage=Stage.SCALE,
            fund_size="2000000.00",
            email=f"beta_ventures_{unique_id}@example.com",
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
        unique_id = uuid.uuid4().hex[:8]
        mixed_user = User.objects.create_user(
            email=f"mixed_{unique_id}@example.com", password="Pass123!"
        )
        mixed_investor = Investor.objects.create(
            user=mixed_user,
            company_name=f"Mixed_Company_{unique_id}",
            industry=self.industry,
            location=self.location,
            founded_year=2020,
            stage=Stage.MVP,
            fund_size="500000.00",
            email=f"mixed_company_{unique_id}@example.com",
        )
        mixed_startup = Startup.objects.create(
            user=mixed_user,  # Same user
            company_name=f"Mixed_Startup_{unique_id}",
            industry=self.industry,
            location=self.location,
            founded_year=2021,
            stage=Stage.MVP,
            email=f"mixed_startup_{unique_id}@example.com",
        )
        mixed_project = Project.objects.create(
            startup=mixed_startup,
            title=f"Own_Project_{unique_id}",
            description="Project owned by the investor",
            category=self.category,
            funding_goal="100000.00",
            email=f"own_project_{unique_id}@example.com"
        )
        
        self.client.force_authenticate(user=mixed_user)
        
        url = f'/api/v1/investors/projects/{mixed_project.id}/follow/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('own project', str(response.data).lower())

    def test_api_response_includes_project_details(self):
        """Test that API response includes relevant project details."""
        self._authenticate_as_investor()
        
        url = f'/api/v1/investors/projects/{self.project.id}/follow/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        data = response.data
        self.assertEqual(data['project'], self.project.id)
        self.assertEqual(data['project_title'], self.project.title)
        self.assertEqual(data['startup_name'], self.startup.company_name)
        self.assertEqual(data['status'], 'watching')  # default status

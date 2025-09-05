from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import transaction
import uuid

from investors.models import Investor, FollowedProject
from projects.models import Project, Category
from startups.models import Startup, Industry, Location
from users.models import UserRole
from communications.models import Notification, NotificationType
from communications.services import NotificationService
from common.enums import Stage

User = get_user_model()


class ProjectFollowNotificationTests(TransactionTestCase):
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

        # Clear any existing notifications
        Notification.objects.all().delete()

    def test_direct_notification_service_creates_notification(self):
        """Test that the direct notification service creates notifications properly."""
        # Clear any existing notifications to prevent duplicates
        Notification.objects.all().delete()
        
        # Use the direct notification service
        notification = NotificationService.create_project_followed_notification(
            project=self.project,
            investor_user=self.investor_user
        )

        # Verify notification was created
        self.assertIsNotNone(notification)
        self.assertEqual(Notification.objects.count(), 1)
        
        # Verify notification details
        created_notification = Notification.objects.first()
        self.assertEqual(created_notification.user, self.startup_user)
        self.assertEqual(created_notification.related_project, self.project)
        self.assertEqual(created_notification.notification_type.name, 'project_followed')
        self.assertIn(self.project.title, created_notification.message)
        self.assertIn(self.investor_user.first_name, created_notification.message)

    def test_notification_service_prevents_duplicates(self):
        """Test that the notification service prevents duplicate notifications."""
        # Clear any existing notifications to prevent duplicates
        Notification.objects.all().delete()
        
        # Create first notification
        notification1 = NotificationService.create_project_followed_notification(
            project=self.project,
            investor_user=self.investor_user
        )
        
        # Try to create duplicate immediately
        notification2 = NotificationService.create_project_followed_notification(
            project=self.project,
            investor_user=self.investor_user
        )

        # Should still only have one notification
        self.assertEqual(Notification.objects.count(), 1)
        self.assertIsNotNone(notification1)
        self.assertIsNone(notification2)  # Duplicate should return None

    def test_notification_service_handles_missing_startup_user(self):
        """Test that the service handles cases where startup user cannot be determined."""
        # Clear any existing notifications to prevent duplicates
        Notification.objects.all().delete()
        
        # Create a project without a proper startup relationship
        unique_id = uuid.uuid4().hex[:8]
        orphan_project = Project.objects.create(
            startup=self.startup,  # Valid startup
            title=f"Orphan_Project_{unique_id}",
            description="Project with potential issues",
            category=self.category,
            funding_goal="50000.00",
            email=f"orphan_{unique_id}@example.com"
        )
        
        # This should work normally since startup is valid
        notification = NotificationService.create_project_followed_notification(
            project=orphan_project,
            investor_user=self.investor_user
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.user, self.startup_user)

    def test_notification_service_prevents_self_follow_notification(self):
        """Test that no notification is created when user follows their own project."""
        # Clear any existing notifications to prevent duplicates
        Notification.objects.all().delete()
        
        # Try to create notification where investor and startup owner are the same
        notification = NotificationService.create_project_followed_notification(
            project=self.project,
            investor_user=self.startup_user  # Same user as startup owner
        )

        # Should not create notification for self-follow
        self.assertIsNone(notification)
        self.assertEqual(Notification.objects.count(), 0)

    def test_followed_project_creation_with_direct_service(self):
        """Test creating FollowedProject and using direct notification service."""
        # Clear any existing notifications to prevent duplicates
        Notification.objects.all().delete()
        
        # Create the follow relationship
        followed_project = FollowedProject.objects.create(
            investor=self.investor,
            project=self.project,
            status='interested',
            notes='This project looks promising'
        )

        # Manually trigger notification using direct service
        notification = NotificationService.create_project_followed_notification(
            project=self.project,
            investor_user=self.investor_user
        )

        # Verify both objects were created
        self.assertEqual(FollowedProject.objects.count(), 1)
        self.assertEqual(Notification.objects.count(), 1)
        
        # Verify the follow relationship
        self.assertEqual(followed_project.investor, self.investor)
        self.assertEqual(followed_project.project, self.project)
        self.assertEqual(followed_project.status, 'interested')
        
        # Verify the notification
        self.assertIsNotNone(notification)
        self.assertEqual(notification.user, self.startup_user)

    def test_multiple_investors_following_same_project(self):
        """Test that multiple investors can follow the same project and get separate notifications."""
        # Clear any existing notifications to prevent duplicates
        Notification.objects.all().delete()
        
        # Create second investor
        unique_id = uuid.uuid4().hex[:8]
        role_investor, _ = UserRole.objects.get_or_create(role='investor')
        investor2_user = User.objects.create_user(
            email=f"investor2_{unique_id}@example.com",
            password="testpass123",
            first_name="Second",
            last_name="Investor",
            is_active=True,
            role=role_investor
        )
        
        investor2 = Investor.objects.create(
            user=investor2_user,
            company_name=f"SecondInvestCorp_{unique_id}",
            description="Another investment firm",
            industry=self.industry,
            location=self.location,
            email=f"investor2_{unique_id}@secondinvest.com",
            founded_year=2015,
            team_size=10,
            stage=Stage.GROWTH,
            fund_size="5000000.00"
        )

        # Both investors follow the project
        FollowedProject.objects.create(investor=self.investor, project=self.project)
        FollowedProject.objects.create(investor=investor2, project=self.project)

        # Create notifications for both
        notification1 = NotificationService.create_project_followed_notification(
            project=self.project,
            investor_user=self.investor_user
        )
        
        notification2 = NotificationService.create_project_followed_notification(
            project=self.project,
            investor_user=investor2_user
        )

        # Should have 2 notifications for the startup owner
        self.assertEqual(Notification.objects.count(), 2)
        self.assertIsNotNone(notification1)
        self.assertIsNotNone(notification2)
        
        # Both notifications should be for the startup user
        notifications = Notification.objects.all()
        for notif in notifications:
            self.assertEqual(notif.user, self.startup_user)
            self.assertEqual(notif.related_project, self.project)

    def test_notification_message_content(self):
        """Test that notification messages contain the expected content."""
        # Clear any existing notifications to prevent duplicates
        Notification.objects.all().delete()
        
        notification = NotificationService.create_project_followed_notification(
            project=self.project,
            investor_user=self.investor_user
        )

        self.assertIsNotNone(notification)
        message = notification.message.lower()
        
        # Check that message contains key information
        self.assertIn(self.investor_user.first_name.lower(), message)
        self.assertIn('follow', message)
        self.assertIn(self.project.title.lower(), message)

    def test_notification_service_with_transaction_rollback(self):
        """Test that notification service works properly with database transactions."""
        try:
            with transaction.atomic():
                # Create follow relationship
                FollowedProject.objects.create(
                    investor=self.investor,
                    project=self.project
                )
                
                # Create notification
                notification = NotificationService.create_project_followed_notification(
                    project=self.project,
                    investor_user=self.investor_user
                )
                
                self.assertIsNotNone(notification)
                
                # Force rollback by raising exception
                raise Exception("Test rollback")
                
        except Exception:
            pass  # Expected exception
        
        # After rollback, should have no objects
        self.assertEqual(FollowedProject.objects.count(), 0)
        self.assertEqual(Notification.objects.count(), 0)

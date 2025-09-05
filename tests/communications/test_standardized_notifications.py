from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
import uuid

from investors.models import Investor, FollowedProject, SavedStartup
from projects.models import Project, Category
from startups.models import Startup, Industry, Location
from users.models import UserRole
from communications.models import Notification, NotificationType
from communications.services import NotificationService
from common.enums import Stage

User = get_user_model()


class StandardizedNotificationTests(TransactionTestCase):
    """Test the standardized notification creation approach."""
    reset_sequences = True

    def setUp(self):
        """Set up test data with unique identifiers."""
        unique_id = uuid.uuid4().hex[:8]
        
        # Create required objects
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

    def tearDown(self):
        """Clean up test data."""
        Notification.objects.all().delete()

    def test_direct_notification_service_creation(self):
        """Test creating notifications directly via NotificationService."""
        # Clear any existing notifications
        Notification.objects.all().delete()
        
        notification = NotificationService.create_notification(
            notification_type_code='test_notification',
            recipient_user=self.startup_user,
            title='Test Notification',
            message='This is a test notification',
            triggered_by_user=self.investor_user,
            triggered_by_type='investor'
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.user, self.startup_user)
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.triggered_by_user, self.investor_user)
        
        # Verify notification type was created
        ntype = NotificationType.objects.get(code='test_notification')
        self.assertEqual(ntype.name, 'Test Notification')

    def test_project_followed_notification_via_signal(self):
        """Test that project follow notifications are created via signals."""
        # Clear any existing notifications
        Notification.objects.all().delete()
        
        # Create a FollowedProject - this should trigger the signal
        followed_project = FollowedProject.objects.create(
            investor=self.investor,
            project=self.project
        )
        
        # Check that notification was created
        notifications = Notification.objects.filter(
            user=self.startup_user,
            notification_type__code='project_followed'
        )
        
        self.assertEqual(notifications.count(), 1)
        notification = notifications.first()
        self.assertEqual(notification.triggered_by_user, self.investor_user)
        self.assertIn(self.project.title, notification.message)
        self.assertIn(self.investor_user.first_name, notification.message)

    def test_startup_saved_notification_via_signal(self):
        """Test that startup saved notifications are created via signals."""
        # Clear any existing notifications
        Notification.objects.all().delete()
        
        # Create a SavedStartup - this should trigger the signal
        saved_startup = SavedStartup.objects.create(
            investor=self.investor,
            startup=self.startup
        )
        
        # Check that notification was created
        notifications = Notification.objects.filter(
            user=self.startup_user,
            notification_type__code='startup_saved'
        )
        
        self.assertEqual(notifications.count(), 1)
        notification = notifications.first()
        self.assertEqual(notification.triggered_by_user, self.investor_user)
        self.assertIn('saved your startup', notification.message)

    def test_duplicate_prevention(self):
        """Test that duplicate notifications are prevented."""
        # Clear any existing notifications
        Notification.objects.all().delete()
        
        # Create first notification
        notification1 = NotificationService.create_notification(
            notification_type_code='duplicate_test',
            recipient_user=self.startup_user,
            title='Duplicate Test',
            message='First notification',
            triggered_by_user=self.investor_user
        )
        
        # Try to create duplicate within deduplication window
        notification2 = NotificationService.create_notification(
            notification_type_code='duplicate_test',
            recipient_user=self.startup_user,
            title='Duplicate Test',
            message='Second notification',
            triggered_by_user=self.investor_user
        )
        
        self.assertIsNotNone(notification1)
        self.assertIsNone(notification2)  # Should be None due to deduplication
        
        # Verify only one notification exists
        count = Notification.objects.filter(
            user=self.startup_user,
            notification_type__code='duplicate_test'
        ).count()
        self.assertEqual(count, 1)

    def test_self_notification_prevention(self):
        """Test that self-notifications are prevented."""
        # Clear any existing notifications
        Notification.objects.all().delete()
        
        # Try to create self-notification
        notification = NotificationService.create_notification(
            notification_type_code='self_test',
            recipient_user=self.startup_user,
            title='Self Test',
            message='Self notification',
            triggered_by_user=self.startup_user  # Same user
        )
        
        self.assertIsNone(notification)  # Should be None due to self-prevention
        
        # Verify no notification was created
        count = Notification.objects.filter(
            user=self.startup_user,
            notification_type__code='self_test'
        ).count()
        self.assertEqual(count, 0)

    def test_notification_consistency_across_methods(self):
        """Test that both signal and direct service methods create consistent notifications."""
        # Clear any existing notifications
        Notification.objects.all().delete()
        
        # Create via direct service
        direct_notification = NotificationService.create_project_followed_notification(
            project=self.project,
            investor_user=self.investor_user
        )
        
        # Clear notifications
        Notification.objects.all().delete()
        
        # Create via signal (by creating FollowedProject)
        followed_project = FollowedProject.objects.create(
            investor=self.investor,
            project=self.project
        )
        
        signal_notification = Notification.objects.filter(
            user=self.startup_user,
            notification_type__code='project_followed'
        ).first()
        
        # Both should exist and have similar structure
        self.assertIsNotNone(direct_notification)
        self.assertIsNotNone(signal_notification)
        
        # Compare key fields
        self.assertEqual(direct_notification.user, signal_notification.user)
        self.assertEqual(direct_notification.notification_type.code, signal_notification.notification_type.code)
        self.assertEqual(direct_notification.triggered_by_user, signal_notification.triggered_by_user)

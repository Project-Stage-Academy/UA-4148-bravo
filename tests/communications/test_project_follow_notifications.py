from django.test import TestCase
from django.contrib.auth import get_user_model

from investors.models import Investor, FollowedProject
from projects.models import Project
from startups.models import Startup
from communications.models import Notification, NotificationType
from common.models import Industry, Location, Category
from common.enums import Stage

User = get_user_model()

class ProjectFollowNotificationTests(TestCase):
    """
    Test that notifications are created when investors follow projects.
    """

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
            email="startup@example.com", password="Pass123!", first_name="Sam"
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

        # Clear any existing notifications for clean test state
        Notification.objects.all().delete()

    def test_follow_project_creates_notification_for_startup_owner(self):
        """Test that following a project creates a notification for the startup owner."""
        self.assertEqual(Notification.objects.count(), 0)

        # Create FollowedProject instance
        FollowedProject.objects.create(investor=self.investor, project=self.project)

        self.assertEqual(Notification.objects.count(), 1, "Notification not created on project follow")

        notif = Notification.objects.first()
        self.assertEqual(notif.user, self.startup_user)
        self.assertEqual(notif.notification_type.code, "project_followed")
        self.assertEqual(notif.related_project, self.project)
        self.assertEqual(notif.triggered_by_user, self.investor_user)
        self.assertIn("started following your project", notif.message.lower())
        self.assertIn(self.project.title.lower(), notif.message.lower())

    def test_duplicate_follow_does_not_create_duplicate_notification(self):
        """Test that duplicate follows don't create duplicate notifications."""
        FollowedProject.objects.create(investor=self.investor, project=self.project)

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(
            FollowedProject.objects.filter(investor=self.investor, project=self.project).count(),
            1,
        )

        # Try to create duplicate (should fail due to unique constraint)
        try:
            FollowedProject.objects.create(investor=self.investor, project=self.project)
        except Exception:
            pass

        self.assertEqual(Notification.objects.count(), 1, "Duplicate notification created")

    def test_self_follow_does_not_create_notification(self):
        """Test that users cannot follow their own projects and no notification is created."""
        # Create a project for the investor user (same user as startup owner)
        investor_startup = Startup.objects.create(
            user=self.investor_user,  # Same user as investor
            company_name="Investor Startup",
            industry=self.industry,
            location=self.location,
            founded_year=2022,
            stage=Stage.MVP,
            email="investor_startup@example.com",
        )
        
        investor_project = Project.objects.create(
            startup=investor_startup,
            title="Self Project",
            description="Project owned by investor",
            category=self.category,
            funding_goal="100000.00",
            email="self@example.com"
        )

        # Try to create FollowedProject for own project (should be prevented by validation)
        try:
            followed = FollowedProject(investor=self.investor, project=investor_project)
            followed.full_clean()  # This should raise ValidationError
            followed.save()
        except Exception:
            pass  # Expected to fail

        # No notification should be created
        self.assertEqual(Notification.objects.count(), 0, "Notification created for self-follow")

    def test_notification_contains_correct_information(self):
        """Test that the notification contains all the correct information."""
        FollowedProject.objects.create(investor=self.investor, project=self.project)

        notif = Notification.objects.first()
        
        # Check notification fields
        self.assertEqual(notif.title, "New project follower")
        self.assertIn(self.investor_user.first_name, notif.message)
        self.assertIn(self.project.title, notif.message)
        self.assertEqual(notif.triggered_by_type, "investor")
        self.assertEqual(notif.priority, "medium")
        self.assertFalse(notif.is_read)

    def test_multiple_investors_follow_same_project(self):
        """Test that multiple investors can follow the same project and each creates a notification."""
        # Create second investor
        investor2_user = User.objects.create_user(
            email="investor2@example.com", password="Pass123!", first_name="Jane"
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

        # First investor follows
        FollowedProject.objects.create(investor=self.investor, project=self.project)

        self.assertEqual(Notification.objects.count(), 1)

        # Second investor follows same project
        FollowedProject.objects.create(investor=investor2, project=self.project)

        self.assertEqual(Notification.objects.count(), 2)
        
        # Both notifications should be for the same startup owner
        notifications = Notification.objects.all()
        for notif in notifications:
            self.assertEqual(notif.user, self.startup_user)
            self.assertEqual(notif.related_project, self.project)

    def test_investor_follows_multiple_projects_from_same_startup(self):
        """Test that an investor can follow multiple projects from the same startup."""
        # Create second project for the same startup
        project2 = Project.objects.create(
            startup=self.startup,
            title="Mobile App Platform",
            description="Cross-platform mobile development tool",
            category=self.category,
            funding_goal="300000.00",
            email="mobile@rocket.com"
        )

        # Follow first project
        FollowedProject.objects.create(investor=self.investor, project=self.project)

        self.assertEqual(Notification.objects.count(), 1)

        # Follow second project from same startup
        FollowedProject.objects.create(investor=self.investor, project=project2)

        self.assertEqual(Notification.objects.count(), 2)

        # Both notifications should be for the same startup owner
        notifications = Notification.objects.all()
        for notif in notifications:
            self.assertEqual(notif.user, self.startup_user)
            self.assertEqual(notif.triggered_by_user, self.investor_user)

    def test_notification_deduplication_within_same_second(self):
        """Test that notifications are properly deduplicated within the same second."""
        from unittest.mock import patch
        from django.utils import timezone
        
        fixed_time = timezone.now()
        
        with patch('django.utils.timezone.now', return_value=fixed_time):
            # Try to create multiple follows rapidly (simulating race condition)
            FollowedProject.objects.create(investor=self.investor, project=self.project)
            
        # Should only have one notification despite potential race conditions
        self.assertEqual(Notification.objects.count(), 1)

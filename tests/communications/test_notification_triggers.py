from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import connection, IntegrityError
from rest_framework.test import APIClient
from investors.models import Investor, SavedStartup
from startups.models import Startup, Industry, Location
from communications.models import Notification
import uuid

User = get_user_model()


class NotificationTriggersTests(TransactionTestCase):
    """
    When an investor follows a startup (SavedStartup), a Notification
    should be created for the startup owner.

    We use TransactionTestCase to ensure that the on_commit signal executes.
    """
    reset_sequences = True

    def _sync_ntype_sequence(self): 
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT setval(
                    pg_get_serial_sequence('communications_notificationtype','id'),
                    COALESCE((SELECT MAX(id) FROM communications_notificationtype), 1),
                    TRUE
                );
            """)

    def setUp(self):
        # Use UUID to ensure unique values
        unique_id = uuid.uuid4().hex[:8]
        
        self.industry = Industry.objects.create(name=f"IT_{unique_id}")
        self.location = Location.objects.create(
            country="US", region="CA", city=f"SF_{unique_id}", postal_code="94105"
        )

        self.investor_user = User.objects.create_user(
            email=f"investor_{unique_id}@example.com", 
            password="Pass123!", 
            first_name="Ivan"
        )
        self.investor = Investor.objects.create(
            user=self.investor_user,
            company_name=f"API Capital_{unique_id}",
            industry=self.industry,
            location=self.location,
            founded_year=2020,
            stage="mvp",
            fund_size="1000000.00",
        )

        self.startup_user = User.objects.create_user(
            email=f"owner_{unique_id}@example.com", 
            password="Pass123!", 
            first_name="Owner"
        )
        self.startup = Startup.objects.create(
            user=self.startup_user,
            company_name=f"Rocket_{unique_id}",
            industry=self.industry,
            location=self.location,
            founded_year=2021,
            stage="mvp",
            email=f"rocket_{unique_id}@example.com",
        )
        self.client = APIClient()
        Notification.objects.all().delete()

        self._sync_ntype_sequence()

    def test_follow_creates_notification_for_startup_owner(self):
        self.assertEqual(Notification.objects.count(), 0)

        SavedStartup.objects.create(investor=self.investor, startup=self.startup)

        try:
            connection.commit()
        except Exception:
            pass

        self.assertEqual(Notification.objects.count(), 1, "Notification not created on follow")

        notif = Notification.objects.first()
        self.assertEqual(notif.user, self.startup_user)
        self.assertEqual(notif.notification_type.code, "startup_followed")
        self.assertEqual(int(notif.related_startup_id), int(self.startup.id))
        self.assertIn("followed your startup", notif.message.lower())
        
    def test_duplicate_follow_does_not_create_duplicate_notification(self):
        # Create first follow
        SavedStartup.objects.create(investor=self.investor, startup=self.startup)
        try:
            connection.commit()
        except Exception:
            pass

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(
            SavedStartup.objects.filter(investor=self.investor, startup=self.startup).count(),
            1,
        )

        # Try to create duplicate follow - should raise IntegrityError
        with self.assertRaises(IntegrityError):
            SavedStartup.objects.create(investor=self.investor, startup=self.startup)

        # Notification count should remain 1
        self.assertEqual(Notification.objects.count(), 1, "Duplicate notification created")

from django.urls import reverse
from django.contrib.auth.hashers import make_password
from rest_framework import status
from investors.models import Investor, SavedStartup
from startups.models import Startup
from users.models import User, UserRole
from tests.test_base_case import BaseAPITestCase as BaseInvestorTestCase
from django.test.utils import override_settings


@override_settings(SECURE_SSL_REDIRECT=False)
class SavedStartupLoggingTests(BaseInvestorTestCase):
    def setUp(self):
        super().setUp()

        self.investor = Investor.objects.create(
            user=self.user,
            industry=self.industry,
            company_name="API Capital",
            location=self.location,
            email="api.capital@example.com",
            founded_year=2020,
            team_size=5,
            stage="mvp",
            fund_size="1000000.00",
        )

        role_user = UserRole.objects.get(role="user")
        self.startup_owner = User.objects.create(
            email="startup.owner@example.com",
            password=make_password("Pass123!"),
            first_name="Star",
            last_name="Tup",
            role=role_user,
        )
        self.startup = Startup.objects.create(
            user=self.startup_owner,
            industry=self.industry,
            company_name="Cool Startup",
            location=self.location,
            email="info@coolstartup.com",
            founded_year=2020,
            team_size=10,
            stage="mvp",
        )

        self.list_url = reverse("saved-startup-list")

    def test_create_logs(self):
        with self.assertLogs("investors.views", level="INFO") as cap:
            res = self.client.post(
                self.list_url, {"startup": self.startup.id, "status": "watching"}, format="json"
            )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        msgs = "\n".join(r.getMessage() for r in cap.records)
        self.assertTrue("SavedStartup" in msgs and ("create" in msgs or "created" in msgs))

    def test_update_logs(self):
        obj = SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching")
        url = reverse("saved-startup-detail", args=[obj.id])
        with self.assertLogs("investors.views", level="INFO") as cap:
            res = self.client.patch(url, {"status": "contacted"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        msgs = "\n".join(r.getMessage() for r in cap.records)
        self.assertTrue("SavedStartup" in msgs and ("update" in msgs or "updated" in msgs))

    def test_delete_logs(self):
        obj = SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching")
        url = reverse("saved-startup-detail", args=[obj.id])
        with self.assertLogs("investors.views", level="INFO") as cap:
            res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT, res.data)
        msgs = "\n".join(r.getMessage() for r in cap.records)
        self.assertTrue("SavedStartup" in msgs and ("delete" in msgs or "deleted" in msgs))


    def test_create_logs_missing_startup(self):
        with self.assertLogs("investors.views", level="WARNING") as cap:
            res = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, res.data)
        msgs = "\n".join(r.getMessage() for r in cap.records)
        self.assertIn("missing startup", msgs.lower())

    def test_create_logs_invalid_status(self):
        with self.assertLogs("investors.views", level="WARNING") as cap:
            res = self.client.post(self.list_url, {"startup": self.startup.id, "status": "nope"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, res.data)
        msgs = "\n".join(r.getMessage() for r in cap.records)
        self.assertIn("invalid status", msgs.lower())

    def test_create_logs_own_startup(self):
        own = Startup.objects.create(
            user=self.user,
            industry=self.industry,
            company_name="My Own",
            location=self.location,
            email="me@own.com",
            founded_year=2024,
            team_size=1,
            stage="idea",
        )
        with self.assertLogs("investors.views", level="WARNING") as cap:
            res = self.client.post(self.list_url, {"startup": own.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, res.data)
        msgs = "\n".join(r.getMessage() for r in cap.records)
        self.assertIn("own startup", msgs.lower())

    def test_create_logs_duplicate(self):
        first = self.client.post(self.list_url, {"startup": self.startup.id}, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED, first.data)
        with self.assertLogs("investors.views", level="WARNING") as cap:
            dup = self.client.post(self.list_url, {"startup": self.startup.id}, format="json")
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST, dup.data)
        msgs = "\n".join(r.getMessage() for r in cap.records)
        self.assertIn("duplicate", msgs.lower())

    def test_list_logs_denied_for_non_investor(self):
        role_user = UserRole.objects.get(role="user")
        plain_user = User.objects.create(
            email="plain.logging@example.com",
            password=make_password("Pass123!"),
            first_name="No",
            last_name="Investor",
            role=role_user,
        )
        self.client.force_authenticate(user=plain_user)
        with self.assertLogs("users.permissions", level="WARNING") as cap:
            res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN, res.data)
        msgs = "\n".join(r.getMessage() for r in cap.records)
        self.assertIn("Permission denied", msgs)
        self.assertIn("Not an investor", msgs)

    def test_update_logs_validation_error(self):
        obj = SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching")
        url = reverse("saved-startup-detail", args=[obj.id])
        with self.assertLogs("investors.views", level="WARNING") as cap:
            res = self.client.patch(url, {"status": "bad-status"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, res.data)
        msgs = "\n".join(r.getMessage() for r in cap.records)
        self.assertIn("update validation error", msgs.lower())

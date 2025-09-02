from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.test import TransactionTestCase
from django.db import IntegrityError
from rest_framework import status
from rest_framework.test import APIClient
from investors.models import Investor, SavedStartup
from startups.models import Startup
from users.models import User, UserRole
from tests.test_base_case import BaseAPITestCase as BaseInvestorTestCase
from utils.authenticate_client import authenticate_client
from django.test.utils import override_settings


@override_settings(SECURE_SSL_REDIRECT=False)
class SavedStartupAPITests(BaseInvestorTestCase):
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

    def test_investor_can_create_saved_startup(self):
        res = self.client.post(self.list_url, {"startup": self.startup.id, "status": "watching", "notes": "ok"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(SavedStartup.objects.count(), 1)
        obj = SavedStartup.objects.first()
        self.assertEqual(obj.investor, self.investor)
        self.assertEqual(obj.startup, self.startup)
        self.assertEqual(res.data["investor"], self.investor.id)
        self.assertNotIn("startup", res.data)
        if "startup_name" in res.data:
            self.assertEqual(res.data["startup_name"], self.startup.company_name)

    def test_create_fails_when_startup_missing(self):
        res = self.client.post(self.list_url, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, res.data)
        self.assertIn("startup", res.data)

    def test_create_fails_when_startup_invalid(self):
        res = self.client.post(self.list_url, {"startup": 999999}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, res.data)
        self.assertIn("startup", res.data)

    def test_investor_cannot_save_own_startup(self):
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
        res = self.client.post(self.list_url, {"startup": own.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, res.data)
        self.assertIn("You cannot save your own startup", str(res.data))

    def test_cannot_save_duplicate(self):
        SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching")
        res = self.client.post(self.list_url, {"startup": self.startup.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, res.data)
        self.assertIn("Already saved", str(res.data))

    def test_only_investor_can_save(self):
        role_user = UserRole.objects.get(role="user")
        plain_user = User.objects.create(
            email="plain@example.com",
            password=make_password("Pass123!"),
            first_name="No",
            last_name="Investor",
            role=role_user,
        )
        authenticate_client(self.client, plain_user)
        res = self.client.post(self.list_url, {"startup": self.startup.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN, res.data)
        self.assertIn("you do not have permission to perform this action.", str(res.data['detail']).lower())

    def test_auth_required_on_list(self):
        client = APIClient()
        res = client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_auth_required_on_create(self):
        client = APIClient()
        res = client.post(self.list_url, {"startup": self.startup.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_only_current_investor(self):
        role_user = UserRole.objects.get(role="user")
        other_user = User.objects.create(
            email="investor2@example.com",
            password=make_password("Pass123!"),
            first_name="Petro",
            last_name="Second",
            role=role_user,
        )
        other_investor = Investor.objects.create(
            user=other_user,
            industry=self.industry,
            company_name="Another Capital",
            location=self.location,
            email="another.capital@example.com",
            founded_year=2021,
            team_size=3,
            stage="idea",
            fund_size="500000.00",
        )
        SavedStartup.objects.create(investor=other_investor, startup=self.startup, status="watching")
        my_obj = SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching")
        res = self.client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], my_obj.id)
        self.assertEqual(res.data[0]["investor"], self.investor.id)

    def test_get_detail_returns_expected_fields(self):
        obj = SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching", notes="hi")
        url = reverse("saved-startup-detail", args=[obj.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        self.assertEqual(res.data["id"], obj.id)
        self.assertEqual(res.data["investor"], self.investor.id)
        self.assertNotIn("startup", res.data)
        if "startup_name" in res.data:
            self.assertEqual(res.data["startup_name"], self.startup.company_name)
        self.assertIn("status", res.data)
        self.assertIn("notes", res.data)
        self.assertIn("saved_at", res.data)

    def test_patch_status(self):
        obj = SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching")
        url = reverse("saved-startup-detail", args=[obj.id])
        res = self.client.patch(url, {"status": "contacted"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        obj.refresh_from_db()
        self.assertEqual(obj.status, "contacted")

    def test_invalid_status_choice(self):
        res = self.client.post(self.list_url, {"startup": self.startup.id, "status": "nope"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_saved(self):
        obj = SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching")
        url = reverse("saved-startup-detail", args=[obj.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT, res.data)
        self.assertFalse(SavedStartup.objects.filter(id=obj.id).exists())

    def test_cannot_patch_savedstartup_of_another_investor(self):
        role_user = UserRole.objects.get(role="user")
        other_user = User.objects.create(
            email="other@example.com",
            password=make_password("Pass123!"),
            first_name="Other",
            last_name="Investor",
            role=role_user,
        )
        other_investor = Investor.objects.create(
            user=other_user,
            industry=self.industry,
            company_name="Other Capital",
            location=self.location,
            email="other.cap@example.com",
            founded_year=2021,
            team_size=3,
            stage="idea",
            fund_size="500000.00",
        )
        foreign_obj = SavedStartup.objects.create(investor=other_investor, startup=self.startup, status="watching")
        url = reverse("saved-startup-detail", args=[foreign_obj.id])
        res = self.client.patch(url, {"status": "contacted"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND, res.data)

    def test_cannot_delete_savedstartup_of_another_investor(self):
        role_user = UserRole.objects.get(role="user")
        other_user = User.objects.create(
            email="other2@example.com",
            password=make_password("Pass123!"),
            first_name="Other2",
            last_name="Investor",
            role=role_user,
        )
        other_investor = Investor.objects.create(
            user=other_user,
            industry=self.industry,
            company_name="Other2 Capital",
            location=self.location,
            email="other2.cap@example.com",
            founded_year=2021,
            team_size=3,
            stage="idea",
            fund_size="500000.00",
        )
        foreign_obj = SavedStartup.objects.create(investor=other_investor, startup=self.startup, status="watching")
        url = reverse("saved-startup-detail", args=[foreign_obj.id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND, res.data)
        self.assertTrue(SavedStartup.objects.filter(id=foreign_obj.id).exists())

    def test_cannot_change_investor_or_startup_via_patch(self):
        obj = SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching")
        url = reverse("saved-startup-detail", args=[obj.id])
        payload = {"investor": 999999, "startup": 999999, "status": "contacted"}
        res = self.client.patch(url, payload, format="json")
        self.assertIn(res.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST), res.data)
        obj.refresh_from_db()
        self.assertEqual(obj.investor_id, self.investor.id)
        self.assertEqual(obj.startup_id, self.startup.id)

    def test_create_without_notes_ok(self):
        res = self.client.post(self.list_url, {"startup": self.startup.id, "status": "watching"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        obj = SavedStartup.objects.get(id=res.data["id"])
        self.assertTrue(obj.notes in (None, ""))

    def test_patch_notes_to_null_or_empty(self):
        obj = SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching", notes="x")
        url = reverse("saved-startup-detail", args=[obj.id])
        res = self.client.patch(url, {"notes": None}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK, res.data)
        obj.refresh_from_db()
        self.assertTrue(obj.notes in (None, ""))

    def test_only_investor_can_list(self):
        role_user = UserRole.objects.get(role="user")
        plain_user = User.objects.create(
            email="plain2@example.com",
            password=make_password("Pass123!"),
            first_name="No",
            last_name="Investor",
            role=role_user,
        )
        authenticate_client(self.client, plain_user)
        res = self.client.get(self.list_url)
        self.assertIn(res.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN))

    def test_extra_fields_are_ignored_on_create(self):
        res = self.client.post(
            self.list_url,
            {"startup": self.startup.id, "status": "watching", "notes": "ok", "extra": "zzz"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertNotIn("extra", res.data)

    def test_duplicate_returns_400_not_500(self):
        SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching")
        res = self.client.post(self.list_url, {"startup": self.startup.id, "status": "watching"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST, res.data)


class SavedStartupDBConstraintsTests(TransactionTestCase):
    reset_sequences = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.role_user, _ = UserRole.objects.get_or_create(role="user")

    def setUp(self):
        from startups.models import Industry, Location
        self.industry = Industry.objects.create(name="IT")
        self.location = Location.objects.create(country="US", city="NYC", region="NY")
        self.user = User.objects.create(
            email="dbuser@example.com",
            password=make_password("Pass123!"),
            first_name="Db",
            last_name="User",
            role=self.role_user,
        )
        self.investor = Investor.objects.create(
            user=self.user,
            industry=self.industry,
            company_name="DB Capital",
            location=self.location,
            email="db.cap@example.com",
            founded_year=2020,
            team_size=5,
            stage="mvp",
            fund_size="1000000.00",
        )
        self.owner = User.objects.create(
            email="db.startup@example.com",
            password=make_password("Pass123!"),
            first_name="Db",
            last_name="Startup",
            role=self.role_user,
        )
        self.startup = Startup.objects.create(
            user=self.owner,
            industry=self.industry,
            company_name="DB Startup",
            location=self.location,
            email="db@startup.com",
            founded_year=2020,
            team_size=3,
            stage="mvp",
        )

    def test_unique_constraint_on_investor_startup(self):
        SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching")
        with self.assertRaises(IntegrityError):
            SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="contacted")

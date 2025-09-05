from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.test import TransactionTestCase
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient
from investors.models import Investor, SavedStartup
from startups.models import Startup, Industry, Location
from users.models import UserRole
from common.enums import Stage
from utils.authenticate_client import authenticate_client
import uuid

User = get_user_model()


class SavedStartupTests(TransactionTestCase):
    """Test cases for SavedStartup API endpoints with proper cleanup."""
    
    reset_sequences = True

    def setUp(self):
        """Set up test data with unique identifiers to prevent constraint violations."""
        # Clear any existing data to prevent conflicts
        SavedStartup.objects.all().delete()
        Startup.objects.all().delete()
        Investor.objects.all().delete()
        User.objects.all().delete()
        
        # Use UUID for unique values to prevent constraint violations
        unique_id = uuid.uuid4().hex[:8]
        
        self.client = APIClient()
        self.location = Location.objects.get_or_create(
            country="US", region="CA", city=f"SF_{unique_id}", postal_code="94105"
        )[0]
        self.industry, _ = Industry.objects.get_or_create(name=f"IT_{unique_id}")
        role_investor, _ = UserRole.objects.get_or_create(role="investor")
        self.user = User.objects.create(
            email=f"investor_{unique_id}@example.com",
            password=make_password("Pass123!"),
            first_name="In",
            last_name="Vestor",
            role=role_investor,
            is_active=True,
        )
        self.investor = Investor.objects.create(
            user=self.user,
            industry=self.industry,
            company_name=f"API Capital_{unique_id}",
            location=self.location,
            email=f"api.capital_{unique_id}@example.com",
            founded_year=2020,
            team_size=5,
            stage="mvp",
            fund_size="1000000.00",
        )
        role_user, _ = UserRole.objects.get_or_create(role="user")
        self.startup_owner = User.objects.create(
            email=f"startup.owner_{unique_id}@example.com",
            password=make_password("Pass123!"),
            first_name="Star",
            last_name="Tup",
            role=role_user,
            is_active=True,
        )
        self.startup = Startup.objects.create(
            user=self.startup_owner,
            industry=self.industry,
            company_name=f"Cool Startup_{unique_id}",
            location=self.location,
            email=f"info_{unique_id}@coolstartup.com",
            founded_year=2020,
            team_size=10,
            stage="mvp",
        )
        self.list_url = reverse("saved-startup-list")
        
        # Properly authenticate the investor user
        self.client.force_authenticate(user=self.user)

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
        unique_id = uuid.uuid4().hex[:8]
        own = Startup.objects.create(
            user=self.user,
            industry=self.industry,
            company_name=f"My Own_{unique_id}",
            location=self.location,
            email=f"me_{unique_id}@own.com",
            founded_year=2024,
            team_size=1,
            stage="mvp",
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
        role_user, _ = UserRole.objects.get_or_create(role="user")
        unique_id = uuid.uuid4().hex[:8]
        plain_user = User.objects.create(
            email=f"plain_{unique_id}@example.com",
            password=make_password("Pass123!"),
            first_name="No",
            last_name="Investor",
            role=role_user,
            is_active=True,
        )
        authenticate_client(self.client, plain_user)
        res = self.client.post(self.list_url, {"startup": self.startup.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN, res.data)
        self.assertIn("only authenticated investors are allowed", str(res.data['detail']).lower())

    def test_auth_required_on_list(self):
        client = APIClient()
        res = client.get(self.list_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_auth_required_on_create(self):
        client = APIClient()
        res = client.post(self.list_url, {"startup": self.startup.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_only_current_investor(self):
        role_user, _ = UserRole.objects.get_or_create(role="user")
        unique_id = uuid.uuid4().hex[:8]
        other_user = User.objects.create(
            email=f"investor2_{unique_id}@example.com",
            password=make_password("Pass123!"),
            first_name="Petro",
            last_name="Second",
            role=role_user,
            is_active=True,
        )
        other_investor = Investor.objects.create(
            user=other_user,
            industry=self.industry,
            company_name=f"Other Capital_{unique_id}",
            location=self.location,
            email=f"other_{unique_id}@capital.com",
            founded_year=2021,
            team_size=3,
            stage="mvp",
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
        role_user, _ = UserRole.objects.get_or_create(role="user")
        unique_id = uuid.uuid4().hex[:8]
        other_user = User.objects.create(
            email=f"other_{unique_id}@example.com",
            password=make_password("Pass123!"),
            first_name="Other",
            last_name="Investor",
            is_active=True,
            role=role_user
        )
        other_investor = Investor.objects.create(
            user=other_user,
            industry=self.industry,
            company_name=f"Other Capital_{unique_id}",
            location=self.location,
            email=f"other_{unique_id}@capital.com",
            founded_year=2021,
            team_size=3,
            stage="mvp",
            fund_size="500000.00",
        )
        foreign_obj = SavedStartup.objects.create(investor=other_investor, startup=self.startup, status="watching")
        url = reverse("saved-startup-detail", args=[foreign_obj.id])
        res = self.client.patch(url, {"status": "contacted"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND, res.data)

    def test_cannot_delete_savedstartup_of_another_investor(self):
        role_user, _ = UserRole.objects.get_or_create(role="user")
        other_user = User.objects.create(
            email="other2@example.com",
            password=make_password("Pass123!"),
            first_name="Other2",
            last_name="Investor",
            role=role_user,
            is_active=True,
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
        role_user, _ = UserRole.objects.get_or_create(role="user")
        plain_user = User.objects.create(
            email="plain2@example.com",
            password=make_password("Pass123!"),
            first_name="No",
            last_name="Investor",
            role=role_user,
            is_active=True,
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
        unique_id = uuid.uuid4().hex[:8]
        
        self.industry, _ = Industry.objects.get_or_create(name=f"IT_{unique_id}")
        self.location, _ = Location.objects.get_or_create(
            country="US", region="CA", city=f"SF_{unique_id}", postal_code="94105"
        )
        role_user, _ = UserRole.objects.get_or_create(role="user")
        self.user = User.objects.create(
            email=f"dbuser_{unique_id}@example.com",
            password=make_password("Pass123!"),
            first_name="Db",
            last_name="User",
            role=role_user,
            is_active=True,
        )
        self.investor = Investor.objects.create(
            user=self.user,
            industry=self.industry,
            company_name=f"DB Capital_{unique_id}",
            location=self.location,
            email=f"db.cap_{unique_id}@example.com",
            founded_year=2020,
            team_size=5,
            stage="mvp",
            fund_size="1000000.00",
        )
        self.owner = User.objects.create(
            email=f"db.startup_{unique_id}@example.com",
            password=make_password("Pass123!"),
            first_name="Db",
            last_name="Startup",
            role=role_user,
            is_active=True,
        )
        self.startup = Startup.objects.create(
            user=self.owner,
            industry=self.industry,
            company_name=f"DB Startup_{unique_id}",
            location=self.location,
            email=f"db_{unique_id}@startup.com",
            founded_year=2020,
            team_size=3,
            stage="mvp",
        )

    def test_unique_constraint_on_investor_startup(self):
        SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="watching")
        with self.assertRaises(IntegrityError):
            SavedStartup.objects.create(investor=self.investor, startup=self.startup, status="contacted")

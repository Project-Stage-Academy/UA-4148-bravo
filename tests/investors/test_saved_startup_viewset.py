from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.test.utils import override_settings
from investors.models import Investor, SavedStartup
from startups.models import Startup, Industry, Location
from users.models import UserRole
from unittest.mock import patch


@override_settings(SECURE_SSL_REDIRECT=False)
class SavedStartupViewSetTests(APITestCase):
    """
    Tests for the SavedStartupViewSet registered under the basename 'saved-startup'.

    Endpoints via DefaultRouter:
        - POST   /saved/                 -> create a saved startup
        - GET    /saved/                 -> list current investor's saved startups
        - PATCH  /saved/{id}/            -> partial update (e.g., status, notes)
        - DELETE /saved/{id}/            -> delete a saved startup
    """

    def setUp(self):
        """
        Prepare:
        - roles, users (investor + startup owner)
        - location/industry
        - investor profile for self.user
        - a startup owned by another user
        - authenticate as investor user
        """
        User = get_user_model()

        # roles (many projects pre-seed these; create if missing)
        self.role_user, _ = UserRole.objects.get_or_create(role="user")

        # base data for foreign keys
        self.location = Location.objects.create(country="US", city="NYC", region="NY")
        self.industry = Industry.objects.create(name="FinTech")

        # investor user (the authenticated caller)
        self.user = User.objects.create(
            email="inv@example.com",
            password=make_password("Pass123!"),
            first_name="In",
            last_name="Vestor",
            role=self.role_user,
            is_active=True
        )
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

        # startup owner (another user)
        self.startup_owner = User.objects.create(
            email="startup.owner@example.com",
            password=make_password("Pass123!"),
            first_name="Star",
            last_name="Tup",
            role=self.role_user,
            is_active=True
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

        # router names from: router.register(r'saved', SavedStartupViewSet, basename='saved-startup')
        self.list_url = reverse("saved-startup-list")

        # authenticate as investor user
        self.client.force_authenticate(self.user)

    def test_create_saved_startup_returns_201(self):
        """First save should create a record and return 201 Created."""
        resp = self.client.post(self.list_url, data={"startup": self.startup.id}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            SavedStartup.objects.filter(investor=self.investor, startup=self.startup).count(), 1
        )
        body = resp.json()
        self.assertIsNotNone(body.get("id"))
        self.assertEqual(body.get("startup_name"), self.startup.company_name)

    def test_duplicate_save_returns_400_no_duplicate_row(self):
        """
        Second save of the same startup should NOT create another row.
        Your ViewSet raises ValidationError("Already saved.") -> 400.
        """
        first = self.client.post(self.list_url, data={"startup": self.startup.id}, format="json")
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self.client.post(self.list_url, data={"startup": self.startup.id}, format="json")
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            SavedStartup.objects.filter(investor=self.investor, startup=self.startup).count(), 1
        )

    def test_cannot_save_own_startup_returns_400(self):
        """Investor is not allowed to save their own startup -> 400."""
        my_startup = Startup.objects.create(
            user=self.user,
            industry=self.industry,
            company_name="My Company",
            location=self.location,
            email="me@myco.com",
            founded_year=2021,
            team_size=3,
            stage="mvp",
        )
        resp = self.client.post(self.list_url, data={"startup": my_startup.id}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            SavedStartup.objects.filter(investor=self.investor, startup=my_startup).count(), 0
        )

    def test_list_returns_only_current_investor_items(self):
        """
        Ensure list endpoint returns only rows belonging to the authenticated investor.
        """
        # Create a row for another investor
        User = get_user_model()
        other_user = User.objects.create_user(
            email="other@ex.com",
            password="x",
            role=self.role_user,
            is_active=True
        )
        other_investor = Investor.objects.create(
            user=other_user,
            industry=self.industry,
            company_name="Other Capital",
            location=self.location,
            email="other@ex.com",
            founded_year=2020,
            team_size=2,
            stage="mvp",
            fund_size="0.00",
        )
        SavedStartup.objects.create(investor=other_investor, startup=self.startup)

        # Create our own row
        self.client.post(self.list_url, data={"startup": self.startup.id}, format="json")

        r = self.client.get(self.list_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["startup_name"], self.startup.company_name)

    def test_partial_update_status(self):
        """PATCH should update allowed fields (e.g., status) for own row."""
        # create
        self.client.post(self.list_url, data={"startup": self.startup.id}, format="json")
        obj = SavedStartup.objects.get(investor=self.investor, startup=self.startup)

        url = reverse("saved-startup-detail", args=[obj.id])
        r = self.client.patch(url, data={"status": "contacted"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        obj.refresh_from_db()
        self.assertEqual(obj.status, "contacted")

    def test_invalid_status_returns_400(self):
        """PATCH invalid status should return 400 and not change the row."""
        # create
        self.client.post(self.list_url, data={"startup": self.startup.id}, format="json")
        obj = SavedStartup.objects.get(investor=self.investor, startup=self.startup)

        url = reverse("saved-startup-detail", args=[obj.id])
        r = self.client.patch(url, data={"status": "not-a-valid"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        obj.refresh_from_db()
        self.assertNotEqual(obj.status, "not-a-valid")

    def test_delete_returns_204_and_removes_row(self):
        """DELETE should return 204 No Content and remove the record."""
        self.client.post(self.list_url, data={"startup": self.startup.id}, format="json")
        obj = SavedStartup.objects.get(investor=self.investor, startup=self.startup)

        url = reverse("saved-startup-detail", args=[obj.id])
        r = self.client.delete(url)
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SavedStartup.objects.filter(pk=obj.pk).exists())

    def test_create_missing_startup_field_returns_400(self):
        """POST without 'startup' field should fail with 400."""
        resp = self.client.post(self.list_url, data={}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_requires_investor_profile_returns_403(self):
        """
        get_queryset raises PermissionDenied for non-investors.
        Expect 403 when authenticated user has no investor profile.
        """
        User = get_user_model()
        plain = User.objects.create_user(
            email="plain@ex.com",
            password="x",
            role=self.role_user,
            is_active=True
        )
        self.client.force_authenticate(plain)
        r = self.client.get(self.list_url)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_cannot_update_or_delete_others_row(self, mocked_permission):
        """
        Ensure a different investor cannot update/delete someone else's saved row.
        With get_queryset filtering to current investor, this should 404.
        """
        # create row as self
        self.client.post(self.list_url, data={"startup": self.startup.id}, format="json")
        obj = SavedStartup.objects.get(investor=self.investor, startup=self.startup)

        # switch to another investor
        User = get_user_model()
        other_user = User.objects.create_user(
            email="evil@ex.com",
            password="x",
            role=self.role_user,
            is_active=True
        )
        Investor.objects.create(
            user=other_user,
            industry=self.industry,
            company_name="Evil Capital",
            location=self.location,
            email="evil@ex.com",
            founded_year=2020,
            team_size=2,
            stage="mvp",
            fund_size="0.00",
        )
        self.client.force_authenticate(other_user)

        detail_url = reverse("saved-startup-detail", args=[obj.id])

        # PATCH
        r1 = self.client.patch(detail_url, data={"status": "contacted"}, format="json")
        self.assertEqual(r1.status_code, status.HTTP_404_NOT_FOUND)

        # DELETE
        r2 = self.client.delete(detail_url)
        self.assertEqual(r2.status_code, status.HTTP_404_NOT_FOUND)

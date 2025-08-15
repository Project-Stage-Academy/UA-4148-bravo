from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User, UserRole
from profiles.models import Industry, Location, Startup, Investor
from projects.models import Project, Category
from investments.models import Subscription


class TestSubscriptionCreateAPI(TestCase):
    """Integration tests for the subscription creation endpoint."""

    @classmethod
    def setUpTestData(cls):
        """Set up initial data for all tests."""
        cls.role_investor, _ = UserRole.objects.get_or_create(role='investor')
        cls.role_user, _ = UserRole.objects.get_or_create(role='user')

        cls.investor_user = User.objects.create_user(
            email="investor@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="Investor",
            role=cls.role_investor,
        )
        cls.startup_user = User.objects.create_user(
            email="startup_owner@example.com",
            password="testpassword123",
            first_name="Startup",
            last_name="Owner",
            role=cls.role_user,
        )

        cls.industry = Industry.objects.create(name="Technology")
        cls.location = Location.objects.create(country="US", city="Test City")

        cls.startup = Startup.objects.create(
            user=cls.startup_user,
            industry=cls.industry,
            company_name="Startup Inc",
            location=cls.location,
            email="startup@example.com",
            founded_year=2020,
            team_size=5,
            stage="mvp",
        )

        cls.category = Category.objects.create(name="Fintech")
        cls.project = Project.objects.create(
            startup=cls.startup,
            title="Funding Project",
            funding_goal=Decimal("1000.00"),
            current_funding=Decimal("0.00"),
            category=cls.category,
            email="project@example.com",
        )

    def setUp(self):
        self.client = APIClient()

    def authenticate(self, user):
        """Authenticate API client with the given user."""
        self.client.force_authenticate(user=user)

    def test_create_subscription_success(self):
        """Test successful creation of a subscription by an investor."""
        self.authenticate(self.investor_user)
        url = reverse("subscription-create")
        payload = {"project": self.project.id, "amount": 200}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_funding, Decimal("200.00"))
        self.assertEqual(response.data["remaining_funding"], Decimal("800.00"))
        self.assertEqual(response.data["project_status"], "Partially funded")
        self.assertEqual(Subscription.objects.count(), 1)

    def test_create_subscription_fully_funded(self):
        """Test that the project gets 'Fully funded' status upon reaching its goal."""
        self.project.current_funding = Decimal("900.00")
        self.project.save()
        self.authenticate(self.investor_user)

        url = reverse("subscription-create")
        payload = {"project": self.project.id, "amount": 100}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_funding, Decimal("1000.00"))
        self.assertEqual(response.data["project_status"], "Fully funded")

    def test_create_subscription_exceeds_goal_fails(self):
        """Test that an investment exceeding the goal is blocked."""
        self.authenticate(self.investor_user)
        url = reverse("subscription-create")
        payload = {"project": self.project.id, "amount": 1500}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("exceeds the remaining funding", str(response.data))
        self.assertEqual(Subscription.objects.count(), 0)

    def test_unauthenticated_user_cannot_subscribe(self):
        """Test that an unauthenticated user cannot invest."""
        url = reverse("subscription-create")
        payload = {"project": self.project.id, "amount": 200}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_non_investor_cannot_subscribe(self):
        """Test that a non-investor user cannot create a subscription."""
        self.authenticate(self.startup_user)
        url = reverse("subscription-create")
        payload = {"project": self.project.id, "amount": 100}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_startup_owner_cannot_invest_in_own_project(self):
        """Test that a startup owner cannot invest in their own project."""
        self.startup_user.role = self.role_investor
        self.startup_user.save()
        Investor.objects.create(
            user=self.startup_user,
            industry=self.project.startup.industry,
            company_name="Owner As Investor",
            location=self.project.startup.location,
            email="owner_as_investor@example.com",
            founded_year=2021,
        )

        self.authenticate(self.startup_user)
        url = reverse("subscription-create")
        payload = {"project": self.project.id, "amount": 100}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You cannot invest in your own project", str(response.data))
        self.assertEqual(Subscription.objects.count(), 0)

    def test_invest_in_already_fully_funded_project_fails(self):
        """Test that investing in a fully funded project is blocked."""
        self.project.current_funding = self.project.funding_goal
        self.project.save()
        self.authenticate(self.investor_user)

        url = reverse("subscription-create")
        payload = {"project": self.project.id, "amount": 50}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project is already fully funded", str(response.data))
        self.assertEqual(Subscription.objects.count(), 0)

    def test_invest_with_invalid_amount_fails(self):
        """Test that zero or negative investment amounts are blocked."""
        self.authenticate(self.investor_user)
        url = reverse("subscription-create")

        payload_zero = {"project": self.project.id, "amount": 0}
        response_zero = self.client.post(url, payload_zero, format="json")
        self.assertEqual(response_zero.status_code, status.HTTP_400_BAD_REQUEST)

        payload_negative = {"project": self.project.id, "amount": -100}
        response_negative = self.client.post(url, payload_negative, format="json")
        self.assertEqual(response_negative.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Subscription.objects.count(), 0)

    def test_invest_in_nonexistent_project_fails(self):
        """Test that investing in a non-existent project returns a 400 error."""
        self.authenticate(self.investor_user)
        url = reverse("subscription-create")
        payload = {"project": 9999, "amount": 100}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid pk", str(response.data.get('project')))

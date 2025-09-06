from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import UserRole
from investors.models import Investor
from startups.models import Startup, Industry, Location
from projects.models import Project, Category
from investments.models import Subscription

User = get_user_model()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CELERY_BROKER_URL="memory://",
    CELERY_RESULT_BACKEND="cache+memory://",
    SECURE_SSL_REDIRECT=False
)
class TestSubscriptionPermissions403Policy(TestCase):
    """
    Tests SubscriptionCreateView with the spec policy:
      - any unauthorized access -> 403 Forbidden
      - authenticated non-investor -> 403 Forbidden
      - authenticated investor -> 201 Created and a Subscription is created
    """

    def setUp(self):
        self.client = APIClient()

        # Roles
        self.role_user, _ = UserRole.objects.get_or_create(role="user")
        self.role_investor, _ = UserRole.objects.get_or_create(role="investor")

        # Users
        self.investor_user = User.objects.create(
            email="investor@example.com",
            password=make_password("Pass123!"),
            first_name="In", last_name="Vestor",
            role=self.role_investor, is_active=True,
        )
        self.non_investor_user = User.objects.create(
            email="noninvestor@example.com",
            password=make_password("Pass123!"),
            first_name="Non", last_name="Investor",
            role=self.role_user, is_active=True,
        )
        self.startup_owner = User.objects.create(
            email="owner@example.com",
            password=make_password("Pass123!"),
            first_name="Star", last_name="Tup",
            role=self.role_user, is_active=True,
        )

        # Dictionaries
        self.industry = Industry.objects.create(name="IT")
        self.location = Location.objects.create(country="UA")
        self.category = Category.objects.create(name="Tech")

        # Investor profile
        Investor.objects.create(
            user=self.investor_user,
            industry=self.industry,
            company_name="API Capital",
            location=self.location,
            email="api.capital@example.com",
            founded_year=2020,
            team_size=5,
            stage="mvp",
            fund_size="1000000.00",
        )

        # Startup and project
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
        self.project = Project.objects.create(
            startup=self.startup,
            category=self.category,
            title="Test Project",
            description="Testing subscriptions",
            funding_goal=Decimal("1000.00"),
            current_funding=Decimal("0.00"),
            email="project@coolstartup.com",
        )

        # URL from projects/urls.py
        self.url = reverse("project-subscribe", kwargs={"project_id": self.project.id})

    def test_unauthenticated_gets_403(self):
        """Unauthenticated → 403 Forbidden."""
        resp = self.client.post(self.url, {"amount": "100.00"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, resp.data)

    def test_authenticated_non_investor_gets_403(self):
        """Authenticated non-investor -> 403 Forbidden and no Subscription created."""
        before = Subscription.objects.count()

        self.client.force_authenticate(user=self.non_investor_user)
        resp = self.client.post(self.url, {"amount": "100.00"}, format="json")

        after = Subscription.objects.count()

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN, resp.data)
        self.assertEqual(after, before)  

    def test_authenticated_investor_gets_201_and_subscription_created(self):
        """Authenticated investor → 201 Created and Subscription is created."""
        self.client.force_authenticate(user=self.investor_user)
        before = Subscription.objects.count()

        resp = self.client.post(self.url, {"amount": "100.00"}, format="json")
        after = Subscription.objects.count()

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        self.assertEqual(after, before + 1)
        self.assertIn("message", resp.data)
        self.assertIn("subscription", resp.data)
        self.assertIn("remaining_funding", resp.data)
        self.assertIn("project_status", resp.data)

        # Verify that the project was updated
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_funding, Decimal("100.00"))

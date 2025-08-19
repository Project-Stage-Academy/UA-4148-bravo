from decimal import Decimal
from rest_framework.test import APIClient, APITransactionTestCase
from django.urls import reverse
from rest_framework import status
from common.enums import Stage
from users.models import User, UserRole
from startups.models import Industry, Location, Startup
from investors.models import Investor
from projects.models import Project, Category
from investments.models import Subscription


class TestSubscriptionCreateAPI(APITransactionTestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("subscription-create")

        self.role_user, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
        self.investor_user = User.objects.create_user(
            email="investor@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="Investor",
            role=self.role_user,
        )
        self.startup_user = User.objects.create_user(
            email="startup_owner@example.com",
            password="testpassword123",
            first_name="Startup",
            last_name="Owner",
            role=self.role_user,
        )

        self.industry = Industry.objects.create(name="Technology")
        self.location = Location.objects.create(country="US", city="Test City")

        self.startup = Startup.objects.create(
            user=self.startup_user,
            industry=self.industry,
            company_name="Startup Inc",
            location=self.location,
            email="startup@example.com",
            founded_year=2020,
            team_size=5,
            stage=Stage.MVP,
        )
        self.investor = Investor.objects.create(
            user=self.investor_user,
            industry=self.industry,
            company_name="Investor Inc",
            location=self.location,
            email="investorbit@example.com",
            founded_year=2015,
            team_size=1500,
            stage=Stage.MVP,
            fund_size=Decimal("1000.00"),
        )
        self.category = Category.objects.create(name="Fintech")
        self.project = Project.objects.create(
            startup=self.startup,
            title="Funding Project",
            funding_goal=Decimal("1000.00"),
            current_funding=Decimal("0.00"),
            category=self.category,
            email="project@example.com",
        )

    # ---------- Helpers ----------

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def subscribe(self, user, investor_id, project_id, amount):
        """Helper to authenticate and send a subscription request."""
        self.authenticate(user)
        return self.client.post(
            self.url,
            {"investor": investor_id, "project": project_id, "amount": amount},
            format="json",
        )

    def assertSubscriptionCount(self, expected):
        self.assertEqual(Subscription.objects.count(), expected)

    # ---------- Tests ----------

    def test_create_subscription_success(self):
        response = self.subscribe(self.investor_user, self.investor.id, self.project.id, 200)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_funding, Decimal("200.00"))
        self.assertEqual(response.data["remaining_funding"], Decimal("800.00"))
        self.assertEqual(response.data["project_status"], "Partially funded")
        self.assertSubscriptionCount(1)

    def test_subscription_exactly_funds_project(self):
        """Investor fills the project to its exact funding goal."""
        self.project.current_funding = Decimal("900.00")
        self.project.save()

        response = self.subscribe(self.investor_user, self.investor.id, self.project.id, 100)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_funding, Decimal("1000.00"))
        self.assertEqual(response.data["project_status"], "Fully funded")

    def test_subscription_exceeds_goal_rejected(self):
        response = self.subscribe(self.investor_user, self.investor.id, self.project.id, 1500)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)
        self.assertSubscriptionCount(0)

    def test_unauthenticated_user_cannot_subscribe(self):
        payload = {"investor": self.investor.id, "project": self.project.id, "amount": 200}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertSubscriptionCount(0)

    def test_non_investor_cannot_subscribe(self):
        response = self.subscribe(self.startup_user, self.investor.id, self.project.id, 100)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertSubscriptionCount(0)

    def test_startup_owner_cannot_invest_in_own_project(self):
        Investor.objects.create(
            user=self.startup_user,
            industry=self.industry,
            company_name="Owner As Investor",
            location=self.location,
            email="owner_as_investor@example.com",
            founded_year=2021,
        )

        response = self.subscribe(self.startup_user, self.startup_user.investor.id, self.project.id, 100)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        self.assertSubscriptionCount(0)

    def test_subscription_rejected_if_project_already_funded(self):
        """No one can invest in a fully funded project."""
        self.project.current_funding = self.project.funding_goal
        self.project.save()

        response = self.subscribe(self.investor_user, self.investor.id, self.project.id, 50)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project", response.data)
        self.assertSubscriptionCount(0)

    def test_invest_with_invalid_amount_fails(self):
        for invalid_amount in [0, -100]:
            response = self.subscribe(self.investor_user, self.investor.id, self.project.id, invalid_amount)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertSubscriptionCount(0)

    def test_invest_in_nonexistent_project_fails(self):
        response = self.subscribe(self.investor_user, self.investor.id, 9999, 100)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project", response.data)
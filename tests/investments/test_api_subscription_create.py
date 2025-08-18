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
            fund_size=Decimal("1000.00")
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

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_create_subscription_success(self):
        self.authenticate(self.investor_user)
        url = reverse("subscription-create")
        payload = {
            "investor": self.investor.id,
            "project": self.project.id,
            "amount": 200
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_funding, Decimal("200.00"))
        self.assertEqual(response.data["remaining_funding"], Decimal("800.00"))
        self.assertEqual(response.data["project_status"], "Partially funded")
        self.assertEqual(Subscription.objects.count(), 1)

    def test_create_subscription_fully_funded(self):
        self.project.current_funding = Decimal("900.00")
        self.project.save()
        self.authenticate(self.investor_user)

        url = reverse("subscription-create")
        payload = {
            "investor": self.investor.id,
            "project": self.project.id,
            "amount": 100
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_funding, Decimal("1000.00"))
        self.assertEqual(response.data["project_status"], "Fully funded")

    def test_create_subscription_exceeds_goal_fails(self):
        self.authenticate(self.investor_user)
        url = reverse("subscription-create")
        payload = {
            "investor": self.investor.id,
            "project": self.project.id,
            "amount": 1500
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("exceeds funding goal", str(response.data))
        self.assertEqual(Subscription.objects.count(), 0)

    def test_unauthenticated_user_cannot_subscribe(self):
        url = reverse("subscription-create")
        payload = {
            "investor": self.investor.id,
            "project": self.project.id,
            "amount": 200
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_non_investor_cannot_subscribe(self):
        self.authenticate(self.startup_user)
        url = reverse("subscription-create")
        payload = {
            "investor": self.investor.id,
            "project": self.project.id,
            "amount": 100
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_startup_owner_cannot_invest_in_own_project(self):
        Investor.objects.create(
            user=self.startup_user,
            industry=self.industry,
            company_name="Owner As Investor",
            location=self.location,
            email="owner_as_investor@example.com",
            founded_year=2021,
        )
        self.authenticate(self.startup_user)
        url = reverse("subscription-create")
        payload = {
            "investor": self.startup_user.investor.id,
            "project": self.project.id,
            "amount": 100
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invest in their own", str(response.data))
        self.assertEqual(Subscription.objects.filter(project=self.project).count(), 0)

    def test_invest_in_already_fully_funded_project_fails(self):
        self.project.current_funding = self.project.funding_goal
        self.project.save()
        self.authenticate(self.investor_user)
        url = reverse("subscription-create")
        payload = {
            "investor": self.investor.id,
            "project": self.project.id,
            "amount": 50
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fully funded", str(response.data))
        self.assertEqual(Subscription.objects.count(), 0)

    def test_invest_with_invalid_amount_fails(self):
        self.authenticate(self.investor_user)
        url = reverse("subscription-create")
        payload_zero = {
            "investor": self.investor.id,
            "project": self.project.id,
            "amount": 0
        }
        response_zero = self.client.post(url, payload_zero, format="json")
        self.assertEqual(response_zero.status_code, status.HTTP_400_BAD_REQUEST)

        payload_negative = {
            "investor": self.investor.id,
            "project": self.project.id,
            "amount": -100
        }
        response_negative = self.client.post(url, payload_negative, format="json")
        self.assertEqual(response_negative.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Subscription.objects.count(), 0)

    def test_invest_in_nonexistent_project_fails(self):
        self.authenticate(self.investor_user)
        url = reverse("subscription-create")
        payload = {
            "investor": self.investor.id,
            "project": 9999,
            "amount": 100
        }
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("object does not exist", str(response.data.get('project')))
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from investments.models import Subscription
from tests.test_base_case import BaseAPITestCase
from users.models import UserRole


class TestSubscriptionCreateAPI(BaseAPITestCase):
    """Tests for the subscription creation endpoint."""

    def test_create_subscription_success(self):
        """Successful creation of subscription."""
        url = reverse("subscription-create")
        payload = {"project": self.project.id, "amount": 200}
        self.client.force_authenticate(user=self.investor_user)
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_funding, Decimal("200.00"))
        self.assertEqual(response.data["remaining_funding"], Decimal("800.00"))
        self.assertEqual(response.data["project_status"], "Partially funded")
        self.assertEqual(Subscription.objects.count(), 1)

    def test_create_subscription_fully_funded(self):
        """Project reaches fully funded status."""
        self.project.current_funding = Decimal("900.00")
        self.project.save()

        url = reverse("subscription-create")
        payload = {"project": self.project.id, "amount": 100}
        self.client.force_authenticate(user=self.investor_user)
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.current_funding, Decimal("1000.00"))
        self.assertEqual(response.data["project_status"], "Fully funded")

    def test_create_subscription_exceeds_goal_fails(self):
        """Cannot invest more than the remaining funding."""
        url = reverse("subscription-create")
        self.client.force_authenticate(user=self.investor_user)
        payload = {"project": self.project.id, "amount": 1500}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("exceeds the remaining funding", str(response.data))
        self.assertEqual(Subscription.objects.count(), 0)

    def test_unauthenticated_user_cannot_subscribe(self):
        url = reverse("subscription-create")
        payload = {"project": self.project.id, "amount": 200}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_non_investor_cannot_subscribe(self):
        url = reverse("subscription-create")
        self.client.force_authenticate(user=self.startup_user)
        payload = {"project": self.project.id, "amount": 100}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Subscription.objects.count(), 0)

    def test_startup_owner_cannot_invest_in_own_project(self):
        """Startup owner cannot invest in their own project."""
        url = reverse("subscription-create")
        role_investor, _ = UserRole.objects.get_or_create(role='investor')
        self.startup_user.role = role_investor
        self.startup_user.save()

        from investors.models import Investor
        Investor.objects.create(
            user=self.startup_user,
            industry=self.project.startup.industry,
            company_name="Owner As Investor",
            location=self.project.startup.location,
            email="owner_as_investor@example.com",
            founded_year=2021
        )

        self.client.force_authenticate(user=self.startup_user)
        payload = {"project": self.project.id, "amount": 100}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You cannot invest in your own project", str(response.data))
        self.assertEqual(Subscription.objects.count(), 0)

    def test_invest_in_already_fully_funded_project_fails(self):
        """Cannot invest in fully funded project."""
        self.project.current_funding = self.project.funding_goal
        self.project.save()

        url = reverse("subscription-create")
        payload = {"project": self.project.id, "amount": 50}
        self.client.force_authenticate(user=self.investor_user)
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project is already fully funded", str(response.data))
        self.assertEqual(Subscription.objects.count(), 0)

    def test_invest_with_invalid_amount_fails(self):
        """Check zero or negative investment amount."""
        url = reverse("subscription-create")
        self.client.force_authenticate(user=self.investor_user)

        payload_zero = {"project": self.project.id, "amount": 0}
        response_zero = self.client.post(url, payload_zero, format="json")
        self.assertEqual(response_zero.status_code, status.HTTP_400_BAD_REQUEST)

        payload_negative = {"project": self.project.id, "amount": -100}
        response_negative = self.client.post(url, payload_negative, format="json")
        self.assertEqual(response_negative.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Subscription.objects.count(), 0)

    def test_invest_in_nonexistent_project_fails(self):
        """Investing in non-existent project returns error."""
        url = reverse("subscription-create")
        self.client.force_authenticate(user=self.investor_user)

        payload = {"project": 9999, "amount": 100}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid pk", str(response.data.get('project')))

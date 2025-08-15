from django.core.exceptions import ValidationError
from django.db import IntegrityError
from investments.models import Subscription
from tests.test_base_case import BaseAPITestCase


class SubscriptionModelTests(BaseAPITestCase):

    def test_create_subscription_success(self):
        """Test successful creation of a subscription."""
        sub = self.get_or_create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=200.00,
            investment_share=2.00
        )
        self.assertEqual(sub.amount, 200.00)
        self.assertEqual(sub.investor, self.investor1)
        self.assertEqual(sub.project, self.project)

    def test_unique_investor_project_constraint(self):
        """Test that an investor cannot subscribe to the same project twice."""
        self.get_or_create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=50.00
        )
        with self.assertRaises(IntegrityError) as ctx:
            self.get_or_create_subscription(
                investor=self.investor1,
                project=self.project,
                amount=70.00
            )
        self.assertIn("unique_investor_project", str(ctx.exception))

    def test_amount_min_value_validation(self):
        """Test that the minimum allowed investment amount is 0.01."""
        sub = Subscription(
            investor=self.investor1,
            project=self.project,
            amount=0.00
        )
        with self.assertRaises(ValidationError) as ctx:
            sub.full_clean()
        self.assertIn("Ensure this value is greater than or equal to 0.01", str(ctx.exception))

    def test_investor_cannot_invest_in_own_project(self):
        """Test that an investor cannot invest in their own project."""

        own_startup = self.get_or_create_startup(
            user=self.investor1.user,
            industry=self.industry,
            company_name="Investor Startup",
            location=self.startup_location
        )

        own_project = self.get_or_create_project(
            title="Project Beta",
            startup=own_startup
        )

        sub = Subscription(
            investor=self.investor1,
            project=own_project,
            amount=100.00
        )

        with self.assertRaises(ValidationError) as ctx:
            sub.full_clean()

        self.assertIn(
            "Investors cannot invest in their own startup's project.",
            str(ctx.exception)
        )

    def test_investment_share_value_range(self):
        """Test that investment_share must be between 0.00 and 100.00."""
        sub = Subscription(
            investor=self.investor1,
            project=self.project,
            amount=50.00,
            investment_share=150.00
        )
        with self.assertRaises(ValidationError) as ctx:
            sub.full_clean()
        self.assertIn("Ensure this value is less than or equal to 100", str(ctx.exception))

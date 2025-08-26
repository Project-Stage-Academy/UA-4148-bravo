from decimal import Decimal, ROUND_DOWN
from common.enums import Stage
from investments.services.investment_share_service import recalculate_investment_shares, calculate_investment_share
from tests.test_base_case import BaseAPITestCase


class SubscriptionSerializerValidDataTests(BaseAPITestCase):
    """
    Tests for validating correct behavior of SubscriptionSerializer with valid input data.

    Includes tests for:
    - Typical valid subscription creation
    - Proper rounding of investment shares
    - Handling minimum boundary values
    - Cumulative rounding effects over multiple subscriptions
    """

    def test_subscription_serializer_valid_data(self):
        """Validate serializer with typical valid data."""
        data = self.get_subscription_data(self.investor1, self.project, 250.00)
        serializer = self.serializer_with_user(data, self.investor1.user)
        is_valid = serializer.is_valid()
        if not is_valid:
            print("Validation errors:", serializer.errors)
        self.assertTrue(is_valid, f"Serializer validation failed: {serializer.errors}")

    def test_valid_subscription_creation(self):
        """Test creating a valid subscription with proper amount and investment share."""
        data = self.get_subscription_data(self.investor1, self.project, Decimal("250.00"))
        serializer = self.serializer_with_user(data, self.investor1.user)
        is_valid = serializer.is_valid()
        if not is_valid:
            for field, errors in serializer.errors.items():
                print(f"Validation errors in field '{field}': {errors}")
        self.assertTrue(is_valid, "Serializer validation failed")
        subscription = serializer.save()
        recalculate_investment_shares(self.project)
        subscription.refresh_from_db()
        expected_share = calculate_investment_share(subscription.amount, self.project.funding_goal)
        self.assertAlmostEqual(float(subscription.amount), 250.00, places=2)
        self.assertAlmostEqual(float(subscription.investment_share), float(expected_share), places=2)

    def test_rounding_of_investment_share(self):
        """ Test that the investment_share is correctly rounded for typical decimal amounts. """
        data = self.get_subscription_data(self.investor1, self.project, 333.33)
        serializer = self.serializer_with_user(data, self.investor1.user)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()
        expected_share = (Decimal("333.33") / self.project.funding_goal * 100).quantize(Decimal("0.01"),
                                                                                        rounding=ROUND_DOWN)
        self.assertEqual(subscription.investment_share, expected_share)

    def test_minimum_amount_boundary(self):
        """
        Test that the minimum allowed amount (0.01) is accepted and investment_share calculated correctly.
        """
        data = self.get_subscription_data(self.investor1, self.project, 0.01)
        serializer = self.serializer_with_user(data, self.investor1.user)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()
        expected_share = (Decimal("0.01") / self.project.funding_goal * 100).quantize(Decimal("0.01"))
        self.assertEqual(subscription.investment_share, expected_share)

    def test_cumulative_rounding_errors(self):
        """
        Test multiple small investments that individually round but together should not exceed funding goal.
        """
        self.project.funding_goal = Decimal("100.00")
        self.project.save()
        increments = [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
        subscriptions = []
        for i, amount in enumerate(increments, start=1):
            investor = getattr(self, f'investor{i}', None)
            if not investor:
                user = self.get_or_create_user(f"user{i}@example.com", f"Investor{i}", "Test")
                investor = self.get_or_create_investor(
                    user=user,
                    company_name=f"Investor {i}",
                    fund_size="1000000.00",
                    stage=Stage.SCALE
                )
                setattr(self, f'investor{i}', investor)
            data = self.get_subscription_data(investor, self.project, amount)
            serializer = self.serializer_with_user(data, investor.user)
            self.assertTrue(serializer.is_valid(), serializer.errors)
            subscription = serializer.save()
            subscriptions.append(subscription)
        recalculate_investment_shares(self.project)
        total_share = Decimal("0.00")
        for sub in subscriptions:
            sub.refresh_from_db()
            total_share += sub.investment_share
        self.assertLessEqual(total_share, Decimal("100.00"))
        self.assertGreaterEqual(total_share, Decimal("99.99"))


class SubscriptionSerializerAmountValidationTests(BaseAPITestCase):
    """
    Tests focusing on validation errors related to the 'amount' field
    in SubscriptionSerializer, such as missing, negative, or zero amounts.
    """

    def test_missing_amount_field(self):
        """Ensure serializer rejects subscription missing the 'amount' field."""
        data = self.get_subscription_data(self.investor1, self.project, 250.00)
        data.pop("amount")
        serializer = self.serializer_with_user(data, self.investor1.user)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        self.assertTrue(
            any("required" in str(msg).lower() for msg in serializer.errors["amount"]),
            f"Expected 'required' error message for missing amount, got: {serializer.errors['amount']}"
        )

    def test_negative_amount_is_rejected(self):
        """Ensure negative subscription amounts are rejected."""
        data = self.get_subscription_data(self.investor1, self.project, -100.00)
        serializer = self.serializer_with_user(data, self.investor1.user)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("greater than or equal to" in str(msg).lower() for msg in error_messages),
            f"Expected 'amount' error message about positive value, got: {error_messages}"
        )

    def test_zero_amount_is_rejected(self):
        """Ensure zero subscription amount is rejected."""
        data = self.get_subscription_data(self.investor1, self.project, 0.00)
        serializer = self.serializer_with_user(data, self.investor1.user)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("greater than or equal to" in str(msg).lower() for msg in error_messages),
            f"Expected error message about amount being greater than 0, got: {error_messages}"
        )


class SubscriptionSerializerInvestmentConstraintsTests(BaseAPITestCase):
    """Tests enforcing business logic and investment constraints for Subscriptions."""

    def test_self_investment_rejected(self):
        """Reject self-investment where investor owns the project."""
        self.project.startup.user = self.investor1.user
        self.project.startup.save()
        data = self.get_subscription_data(self.investor1, self.project, Decimal("100.00"))
        serializer = self.serializer_with_user(data, self.investor1.user)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        error_messages = serializer.errors["non_field_errors"]
        self.assertTrue(
            any("cannot invest in their own" in str(msg).lower() for msg in error_messages),
            f"Expected self-investment error, got: {error_messages}"
        )

    def test_exceeds_funding_goal(self):
        """Reject subscription exceeding the funding goal."""
        amount1 = (self.project.funding_goal * Decimal("0.9")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        amount2 = (self.project.funding_goal * Decimal("0.2")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        self.get_or_create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=amount1,
            investment_share=Decimal("90.00")
        )
        data = self.get_subscription_data(
            self.investor2,
            self.project,
            amount2
        )
        serializer = self.serializer_with_user(data, self.investor2.user)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("exceeds funding goal" in str(msg).lower() for msg in error_messages),
            f"Expected 'exceeds funding goal' error message, got: {error_messages}"
        )

    def test_sequential_subscriptions_exceeding_funding_goal(self):
        """Reject second subscription that pushes total above funding goal."""
        amount1 = (self.project.funding_goal * Decimal("0.6")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        first_data = self.get_subscription_data(self.investor1, self.project, amount1)
        amount2 = (self.project.funding_goal * Decimal("0.5")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        second_data = self.get_subscription_data(self.investor2, self.project, amount2)
        serializer1 = self.serializer_with_user(first_data, self.investor1.user)
        self.assertTrue(serializer1.is_valid(), serializer1.errors)
        serializer1.save()
        serializer2 = self.serializer_with_user(second_data, self.investor2.user)
        self.assertFalse(serializer2.is_valid())
        self.assertIn("amount", serializer2.errors)
        error_messages = serializer2.errors["amount"]
        self.assertTrue(
            any("exceeds funding goal" in str(msg).lower() for msg in error_messages),
            f"Expected 'exceeds funding goal' error message, got: {error_messages}"
        )

    def test_fully_funded_project_no_more_subscriptions(self):
        """Reject any subscriptions once project is fully funded."""
        self.get_or_create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=self.project.funding_goal,
            investment_share=Decimal("100.00")
        )
        data = self.get_subscription_data(self.investor2, self.project, Decimal("1.00"))
        serializer = self.serializer_with_user(data, self.investor2.user)
        self.assertFalse(serializer.is_valid())
        self.assertTrue(
            "amount" in serializer.errors or "project" in serializer.errors,
            f"Expected validation error for fully funded project, got: {serializer.errors}"
        )
        error_messages = serializer.errors.get("amount", []) + serializer.errors.get("project", [])
        self.assertTrue(
            any("exceeds funding goal" in str(msg).lower() or "fully funded" in str(msg).lower()
                for msg in error_messages),
            f"Expected 'exceeds funding goal' error message, got: {error_messages}"
        )

    def test_total_investment_share_cannot_exceed_funding_goal(self):
        """Ensure total subscriptions do not exceed the project's funding goal."""
        self.get_or_create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("600000.00")
        )
        self.get_or_create_subscription(
            investor=self.investor2,
            project=self.project,
            amount=Decimal("300000.00")
        )
        user3 = self.get_or_create_user("inv3@example.com", "Investor", "Three")
        investor3 = self.get_or_create_investor(
            user=user3,
            company_name="Investor Three",
            fund_size=Decimal("5000000.00"),
            stage=Stage.LAUNCH
        )
        data = self.get_subscription_data(investor3, self.project, Decimal("200000.00"))
        serializer = self.serializer_with_user(data, investor3.user)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("exceeds funding goal" in str(msg).lower() for msg in error_messages),
            f"Expected 'exceeds funding goal' error message, got: {error_messages}"
        )
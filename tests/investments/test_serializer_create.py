from decimal import Decimal, ROUND_DOWN
from common.enums import Stage
from investments.serializers.subscription_create import SubscriptionCreateSerializer
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
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()

        data = self.get_subscription_data(self.investor1, self.project, Decimal("250.00"))
        serializer = SubscriptionCreateSerializer(data=data)
        is_valid = serializer.is_valid()
        if not is_valid:
            print("Validation errors:", serializer.errors)
        self.assertTrue(is_valid, f"Serializer validation failed: {serializer.errors}")

    def test_valid_subscription_creation(self):
        """Test creating a valid subscription with proper amount and investment share."""
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()

        data = self.get_subscription_data(self.investor1, self.project, Decimal("250.00"))
        serializer = SubscriptionCreateSerializer(data=data)

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
        """Test that the investment_share is correctly rounded for typical decimal amounts."""
        # Ensure project funding_goal is larger than subscription amount
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()

        data = self.get_subscription_data(self.investor1, self.project, Decimal("333.33"))
        serializer = SubscriptionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()

        expected_share = calculate_investment_share(subscription.amount, self.project.funding_goal)
        self.assertEqual(subscription.investment_share, expected_share)

    def test_minimum_amount_boundary(self):
        """
        Test that the minimum allowed amount (0.01) is accepted and investment_share calculated correctly.
        """
        self.project.funding_goal = Decimal("1.00")
        self.project.save()

        data = self.get_subscription_data(self.investor1, self.project, Decimal("0.01"))
        serializer = SubscriptionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()

        expected_share = calculate_investment_share(subscription.amount, self.project.funding_goal)
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
            serializer = SubscriptionCreateSerializer(data=data)
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
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()

        data = self.get_subscription_data(self.investor1, self.project, Decimal("250.00"))
        data.pop("amount")
        serializer = SubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        self.assertTrue(
            any("required" in str(msg).lower() for msg in serializer.errors["amount"]),
            f"Expected 'required' error message for missing amount, got: {serializer.errors['amount']}"
        )

    def test_negative_amount_is_rejected(self):
        """Ensure negative subscription amounts are rejected."""
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()

        data = self.get_subscription_data(self.investor1, self.project, Decimal("-100.00"))
        serializer = SubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("greater than or equal to" in str(msg).lower() for msg in error_messages),
            f"Expected 'amount' error message about positive value, got: {error_messages}"
        )

    def test_zero_amount_is_rejected(self):
        """Ensure zero subscription amount is rejected."""
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()

        data = self.get_subscription_data(self.investor1, self.project, Decimal("0.00"))
        serializer = SubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("greater than or equal to" in str(msg).lower() for msg in error_messages),
            f"Expected error message about amount being greater than 0, got: {error_messages}"
        )



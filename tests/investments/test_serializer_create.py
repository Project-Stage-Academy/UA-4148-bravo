from decimal import Decimal
from rest_framework import serializers
from django.test import TransactionTestCase

from tests.setup_tests_data import TestDataMixin
from tests.test_disable_signal_mixin import DisableSignalsMixin
from investments.serializers.subscription_create import SubscriptionCreateSerializer
from investments.services.investment_share_service import recalculate_investment_shares, calculate_investment_share


class SubscriptionSerializerConcurrencyTests(DisableSignalsMixin, TestDataMixin, TransactionTestCase):
    """
    Tests for validating correct behavior of SubscriptionSerializer with valid input data.
    Includes concurrency-safe behavior with signals disabled.
    """
    reset_sequences = True

    def setUp(self):
        super().setUp()
        self.setup_all()

    def test_subscription_serializer_valid_data(self):
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()
        data = self.get_subscription_data(self.investor1, self.project, Decimal("250.00"))
        serializer = SubscriptionCreateSerializer(data=data)
        is_valid = serializer.is_valid()
        if not is_valid:
            print("Validation errors:", serializer.errors)
        self.assertTrue(is_valid)

    def test_valid_subscription_creation(self):
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()
        data = self.get_subscription_data(self.investor1, self.project, Decimal("250.00"))
        serializer = SubscriptionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()
        recalculate_investment_shares(self.project)
        subscription.refresh_from_db()
        expected_share = calculate_investment_share(subscription.amount, self.project.funding_goal)
        self.assertAlmostEqual(float(subscription.amount), 250.00, places=2)
        self.assertAlmostEqual(float(subscription.investment_share), float(expected_share), places=2)

    def test_rounding_of_investment_share(self):
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()
        data = self.get_subscription_data(self.investor1, self.project, Decimal("333.33"))
        serializer = SubscriptionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()
        expected_share = calculate_investment_share(subscription.amount, self.project.funding_goal)
        self.assertEqual(subscription.investment_share, expected_share)

    def test_minimum_amount_boundary(self):
        self.project.funding_goal = Decimal("1.00")
        self.project.save()
        data = self.get_subscription_data(self.investor1, self.project, Decimal("0.01"))
        serializer = SubscriptionCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()
        expected_share = calculate_investment_share(subscription.amount, self.project.funding_goal)
        self.assertEqual(subscription.investment_share, expected_share)

    def test_cumulative_rounding_errors(self):
        self.project.funding_goal = Decimal("100.00")
        self.project.save()
        increments = [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
        subscriptions = []
        for i, amount in enumerate(increments, start=1):
            investor = getattr(self, f'investor{i}', None)
            if not investor:
                user = self.get_or_create_user(f"user{i}@example.com", f"Investor{i}", "Test")
                investor = self.get_or_create_investor(user, f"Investor {i}", Stage.MVP, "1000000.00")
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


class SubscriptionSerializerAmountValidationTests(DisableSignalsMixin, TestDataMixin, TransactionTestCase):
    """
    Tests focusing on validation errors related to the 'amount' field
    in SubscriptionSerializer, with signals disabled.
    """

    def setUp(self):
        super().setUp()
        self.setup_all()

    def test_missing_amount_field(self):
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()
        data = self.get_subscription_data(self.investor1, self.project, Decimal("250.00"))
        data.pop("amount")
        serializer = SubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        self.assertTrue(
            any("required" in str(msg).lower() for msg in serializer.errors["amount"])
        )

    def test_negative_amount_is_rejected(self):
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()
        data = self.get_subscription_data(self.investor1, self.project, Decimal("-100.00"))
        serializer = SubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        self.assertTrue(
            any("greater than or equal to" in str(msg).lower() for msg in serializer.errors["amount"])
        )

    def test_zero_amount_is_rejected(self):
        self.project.funding_goal = Decimal("1000.00")
        self.project.save()
        data = self.get_subscription_data(self.investor1, self.project, Decimal("0.00"))
        serializer = SubscriptionCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        self.assertTrue(
            any("greater than or equal to" in str(msg).lower() for msg in serializer.errors["amount"])
        )






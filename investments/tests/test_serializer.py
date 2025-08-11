import threading
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers
from investments.serializers import SubscriptionSerializer
from tests.test_setup import BaseInvestmentTestCase


class SubscriptionSerializerValidDataTests(BaseInvestmentTestCase):

    def test_subscription_serializer_valid_data(self):
        """Validate serializer with typical valid data."""
        data = self.get_subscription_data(self.investor1, self.project, 250.00)
        serializer = SubscriptionSerializer(data=data)
        is_valid = serializer.is_valid()
        if not is_valid:
            print("Validation errors:", serializer.errors)
        self.assertTrue(is_valid, f"Serializer validation failed: {serializer.errors}")

    def test_valid_subscription_creation(self):
        """Test creating a valid subscription with proper amount and share."""
        data = self.get_subscription_data(self.investor1, self.project, 250.00)
        serializer = SubscriptionSerializer(data=data)
        is_valid = serializer.is_valid()
        if not is_valid:
            for field, errors in serializer.errors.items():
                print(f"Validation errors in field '{field}': {errors}")
        self.assertTrue(is_valid, "Serializer validation failed")

        subscription = serializer.save()
        self.assertAlmostEqual(float(subscription.amount), 250.00, places=2)
        self.assertAlmostEqual(float(subscription.investment_share), 2.50, places=2)

    def test_rounding_of_investment_share(self):
        """
        Test that the investment_share is correctly rounded for typical decimal amounts.
        """
        data = self.get_subscription_data(self.investor1, self.project, 333.33)
        serializer = SubscriptionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()
        self.assertEqual(subscription.investment_share, Decimal("3.33"))

    def test_minimum_amount_boundary(self):
        """
        Test that the minimum allowed amount (0.01) is accepted and investment_share calculated correctly.
        """
        data = self.get_subscription_data(self.investor1, self.project, Decimal("0.01"))
        serializer = SubscriptionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()
        expected_share = (Decimal("0.01") / self.project.funding_goal * 100).quantize(Decimal("0.01"))
        self.assertEqual(subscription.investment_share, expected_share)

    def test_cumulative_rounding_errors(self):
        """
        Test multiple small investments that individually round but together should not exceed funding goal.
        This ensures that cumulative rounding errors do not cause validation issues.
        """
        increments = [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
        total_share = Decimal("0.00")

        for i, amount in enumerate(increments, start=1):
            investor = getattr(self, f'investor{i}', None)
            if not investor:
                user = self.create_user(f"user{i}@example.com", f"Investor{i}", "Test")
                investor = self.create_investor(user=user, company_name=f"Investor {i}", fund_size="1000000.00")
                setattr(self, f'investor{i}', investor)
            data = self.get_subscription_data(investor, self.project, amount)
            serializer = SubscriptionSerializer(data=data)
            self.assertTrue(serializer.is_valid(), serializer.errors)
            subscription = serializer.save()
            total_share += subscription.investment_share

        self.assertLessEqual(total_share, Decimal("100.00"))
        self.assertGreater(total_share, Decimal("99.99"))


class SubscriptionSerializerAmountValidationTests(BaseInvestmentTestCase):

    def test_missing_amount_field(self):
        """Ensure serializer rejects subscription missing the 'amount' field."""
        data = self.get_subscription_data(self.investor1, self.project, 250.00)
        data.pop("amount")
        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        self.assertTrue(
            any("required" in str(msg).lower() for msg in serializer.errors["amount"]),
            f"Expected 'required' error message for missing amount, got: {serializer.errors['amount']}"
        )

    def test_negative_amount_is_rejected(self):
        """Ensure negative subscription amounts are rejected."""
        data = self.get_subscription_data(self.investor1, self.project, -100.00)
        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("must be greater than 0" in str(msg).lower() for msg in error_messages),
            f"Expected 'amount' error message about positive value, got: {error_messages}"
        )

    def test_zero_amount_is_rejected(self):
        """Ensure zero subscription amount is rejected."""
        data = self.get_subscription_data(self.investor1, self.project, 0.00)
        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("greater than 0" in str(msg).lower() for msg in error_messages),
            f"Expected error message about amount being greater than 0, got: {error_messages}"
        )


class SubscriptionSerializerInvestmentConstraintsTests(BaseInvestmentTestCase):

    def test_self_investment_rejected(self):
        """Reject self-investment where investor owns the project."""
        data = self.get_subscription_data(self.investor1, self.project, 100.00)
        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("investor", serializer.errors)

        error_messages = serializer.errors["investor"]
        self.assertTrue(
            any("self-investment" in str(msg).lower() or "cannot invest in own project" in str(msg).lower() for msg in
                error_messages),
            f"Expected self-investment error in 'investor' field, got: {error_messages}"
        )

    def test_exceeds_funding_goal(self):
        """Reject subscription exceeding the funding goal."""
        self.create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=self.project.funding_goal * Decimal("0.9"),
            investment_share=Decimal("90.00")
        )
        data = self.get_subscription_data(
            self.investor2,
            self.project,
            str(self.project.funding_goal * Decimal("0.2"))
        )
        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("exceeds funding goal" in str(msg).lower() for msg in error_messages),
            f"Expected 'exceeds funding goal' error message, got: {error_messages}"
        )

    def test_sequential_subscriptions_exceeding_funding_goal(self):
        """Reject second subscription that pushes total above funding goal."""
        first_data = self.get_subscription_data(
            self.investor1,
            self.project,
            str(self.project.funding_goal * Decimal("0.6"))
        )
        serializer1 = SubscriptionSerializer(data=first_data)
        self.assertTrue(serializer1.is_valid(), serializer1.errors)
        serializer1.save()

        second_data = self.get_subscription_data(
            self.investor2,
            self.project,
            str(self.project.funding_goal * Decimal("0.5"))
        )
        serializer2 = SubscriptionSerializer(data=second_data)
        self.assertFalse(serializer2.is_valid())
        self.assertIn("amount", serializer2.errors)

        error_messages = serializer2.errors["amount"]
        self.assertTrue(
            any("exceeds funding goal" in str(msg).lower() for msg in error_messages),
            f"Expected 'exceeds funding goal' error message, got: {error_messages}"
        )

    def test_fully_funded_project_no_more_subscriptions(self):
        """Reject any subscriptions once project is fully funded."""
        self.create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=self.project.funding_goal,
            investment_share=Decimal("100.00")
        )
        data = self.get_subscription_data(self.investor1, self.project, 1.00)
        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("project", serializer.errors)

        error_messages = serializer.errors["project"]
        self.assertIn(
            "Project is fully funded. No further subscriptions allowed.",
            error_messages,
            f"Expected exact error message for fully funded project, got: {error_messages}"
        )

        amount_errors = serializer.errors.get("amount", [])
        self.assertTrue(
            any("exceeds funding goal" in str(msg).lower() for msg in amount_errors),
            f"Expected 'exceeds funding goal' error message, got: {amount_errors}"
        )

    def test_total_investment_share_cannot_exceed_100_percent(self):
        """Ensure total investment share does not exceed 100%."""
        self.create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("6000.00"),
            investment_share=Decimal("60.00")
        )
        self.create_subscription(
            investor=self.investor2,
            project=self.project,
            amount=Decimal("3000.00"),
            investment_share=Decimal("30.00")
        )

        user3 = self.create_user("inv3@example.com", "Investor", "Three")
        investor3 = self.create_investor(
            user=user3,
            company_name="Investor Three",
            fund_size="500000.00"
        )
        data = self.get_subscription_data(investor3, self.project, 2000.00)
        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("exceeds funding goal" in str(msg).lower() for msg in error_messages),
            f"Expected 'exceeds funding goal' error message, got: {error_messages}"
        )


class SubscriptionSerializerUpdateTests(BaseInvestmentTestCase):

    def test_update_subscription_amount_successfully(self):
        """Allow updating subscription amount and recalculate share."""
        subscription = self.create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("2.00")
        )
        data = self.get_subscription_data(None, None, 500.00)

        serializer = SubscriptionSerializer(subscription, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertAlmostEqual(updated.amount, Decimal("500.00"))
        self.assertAlmostEqual(updated.investment_share, Decimal("5.00"))
        self.assertEqual(updated.investor, subscription.investor)
        self.assertEqual(updated.project, subscription.project)

    def test_update_subscription_amount_unchanged(self):
        """Updating with the same amount keeps investment share unchanged."""
        subscription = self.create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("2.00")
        )
        data = self.get_subscription_data(None, None, 200.00)

        serializer = SubscriptionSerializer(subscription, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertAlmostEqual(updated.amount, Decimal("200.00"))
        self.assertAlmostEqual(updated.investment_share, Decimal("2.00"))

    def test_update_subscription_without_amount_field(self):
        """Partial update without amount leaves subscription unchanged."""
        subscription = self.create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("2.00")
        )

        data = {}

        serializer = SubscriptionSerializer(subscription, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertAlmostEqual(updated.amount, Decimal("200.00"))
        self.assertAlmostEqual(updated.investment_share, Decimal("2.00"))

    def test_cannot_change_investor_on_update(self):
        """Prohibit changing investor on subscription update."""
        subscription = self.create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("2.00")
        )
        other_investor = self.investor2

        data = self.get_subscription_data(
            other_investor.pk,
            subscription.project.pk,
            100.00
        )

        serializer = SubscriptionSerializer(subscription, data=data, partial=True)

        with self.assertRaises(serializers.ValidationError) as context:
            serializer.save()

        self.assertIn("investor", context.exception.detail)

    def test_cannot_change_project_on_update(self):
        """Prohibit changing project on subscription update."""
        subscription = self.create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("2.00")
        )
        new_project = self.create_project(
            title="Other Project",
            funding_goal="20000.00"
        )
        data = self.get_subscription_data(None, new_project.pk, 100.00)

        serializer = SubscriptionSerializer(
            subscription,
            data=self.get_subscription_data(
                subscription.investor.pk,
                new_project.pk,
                data.get("amount", subscription.amount)
            ),
            partial=True
        )

        with self.assertRaises(serializers.ValidationError) as context:
            serializer.save()

        self.assertIn("project", context.exception.detail)


class SubscriptionSerializerConcurrencyTests(BaseInvestmentTestCase):

    def test_concurrent_subscriptions(self):
        """
        Simulate two investors attempting to subscribe concurrently to the same project.
        Verify that the total subscribed amount does not exceed the funding goal,
        and that the second subscription fails if funding goal is reached.
        """
        amount1 = self.project.funding_goal * Decimal("0.6")
        amount2 = self.project.funding_goal * Decimal("0.5")

        errors = []

        def subscribe(investor, amount):
            data = self.get_subscription_data(investor, self.project, amount)
            serializer = SubscriptionSerializer(data=data)
            try:
                with transaction.atomic():
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
            except serializers.ValidationError as e:
                errors.append(e.detail)

        t1 = threading.Thread(target=subscribe, args=(self.investor1, amount1))
        t2 = threading.Thread(target=subscribe, args=(self.investor2, amount2))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        total = self.project.subscription_set.aggregate(
            total_amount=Sum('amount')
        )['total_amount'] or Decimal("0")

        self.assertLessEqual(total, self.project.funding_goal)

        error_messages = [str(e).lower() for error in errors for e in (error.get('amount') or [])]
        self.assertTrue(
            any("exceeds funding goal" in msg for msg in error_messages),
            f"Expected funding goal exceeded error, got: {error_messages}"
        )

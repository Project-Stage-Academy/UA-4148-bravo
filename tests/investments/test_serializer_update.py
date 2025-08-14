from decimal import Decimal
from rest_framework import serializers
from investments.serializers.subscription_update import SubscriptionUpdateSerializer
from tests.test_base_case import BaseAPITestCase

class SubscriptionSerializerUpdateTests(BaseAPITestCase):
    """
    Tests for updating existing Subscription instances through the serializer.
    Covers:
        - Successful amount updates and share recalculation
        - No change when amount remains the same
        - Partial updates without amount field
        - Restrictions on changing investor or project during update
    """

    def test_update_subscription_amount_successfully(self):
        """Allow updating subscription amount and recalculate share."""
        subscription = self.get_or_create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("0.02")
        )
        data = {"amount": Decimal("500.00")}

        serializer = SubscriptionUpdateSerializer(subscription, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.amount, Decimal("500.00"))
        self.assertAlmostEqual(updated.investment_share * 100, Decimal("5.00"))
        self.assertEqual(updated.investor, subscription.investor)
        self.assertEqual(updated.project, subscription.project)

    def test_update_subscription_amount_unchanged(self):
        """Updating with the same amount keeps investment share unchanged."""
        subscription = self.get_or_create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("0.02")
        )
        data = {"amount": Decimal("200.00")}

        serializer = SubscriptionUpdateSerializer(subscription, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.amount, Decimal("200.00"))
        self.assertEqual(updated.investment_share * 100, Decimal("2.00"))

    def test_update_subscription_without_amount_field(self):
        """Partial update without amount leaves subscription unchanged."""
        subscription = self.get_or_create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("0.02")
        )
        data = {}

        serializer = SubscriptionUpdateSerializer(subscription, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()

        self.assertEqual(updated.amount, Decimal("200.00"))
        self.assertEqual(updated.investment_share * 100, Decimal("2.00"))

    def test_cannot_change_investor_on_update(self):
        """Prohibit changing investor on subscription update."""
        subscription = self.get_or_create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("0.02")
        )
        data = {"investor": self.investor2.id, "amount": Decimal("100.00")}

        serializer = SubscriptionUpdateSerializer(subscription, data=data, partial=True)
        with self.assertRaises(serializers.ValidationError) as context:
            serializer.is_valid(raise_exception=True)

        self.assertIn("investor", context.exception.detail)

    def test_cannot_change_project_on_update(self):
        """Prohibit changing project on subscription update."""
        subscription = self.get_or_create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("0.02")
        )
        new_project = self.get_or_create_project(
            title="Other Project",
            funding_goal=Decimal("20000.00")
        )
        data = {"project": new_project.id, "amount": Decimal("100.00")}

        serializer = SubscriptionUpdateSerializer(subscription, data=data, partial=True)
        with self.assertRaises(serializers.ValidationError) as context:
            serializer.is_valid(raise_exception=True)

        self.assertIn("project", context.exception.detail)

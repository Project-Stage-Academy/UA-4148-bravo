from decimal import Decimal

from rest_framework import serializers
from investments.models import Subscription
from investments.serializers import SubscriptionSerializer
from investments.tests.test_setup import BaseInvestmentTestCase
from investors.models import Investor
from projects.models import Project


class SubscriptionSerializerTest(BaseInvestmentTestCase):

    def test_valid_subscription_creation(self):
        data = {
            "investor": self.investor1.pk,
            "project": self.project.pk,
            "amount": "250.00"
        }

        serializer = SubscriptionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()
        self.assertEqual(subscription.amount, Decimal("250.00"))
        self.assertEqual(subscription.investment_share, Decimal("2.50"))

    def test_negative_amount_is_rejected(self):
        data = {
            "investor": self.investor1.pk,
            "project": self.project.pk,
            "amount": "-100.00"
        }

        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_self_investment_rejected(self):
        self.startup_investor = Investor.objects.create(
            user=self.user_startup,
            industry=self.industry,
            location=self.location,
            company_name="Startup VC",
            email="startup@example.com",
            founded_year=2010,
            team_size=3,
            stage="seed",
            fund_size=Decimal("10000.00")
        )

        data = {
            "investor": self.startup_investor.pk,
            "project": self.project.pk,
            "amount": "100.00"
        }

        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("investor", serializer.errors)

    def test_exceeds_funding_goal(self):
        Subscription.objects.create(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("9000.00"),
            investment_share=Decimal("90.00")
        )

        data = {
            "investor": self.investor2.pk,
            "project": self.project.pk,
            "amount": "2000.00"
        }

        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_fully_funded_project_no_more_subscriptions(self):
        Subscription.objects.create(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("10000.00"),
            investment_share=Decimal("100.00")
        )

        data = {
            "investor": self.investor2.pk,
            "project": self.project.pk,
            "amount": "1.00"
        }

        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("project", serializer.errors)

    def test_update_subscription_successfully(self):
        subscription = Subscription.objects.create(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("2.00")
        )

        data = {
            "amount": "500.00"
        }

        serializer = SubscriptionSerializer(subscription, data=data, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.amount, Decimal("500.00"))
        self.assertEqual(updated.investment_share, Decimal("5.00"))

    def test_cannot_change_project_on_update(self):
        subscription = Subscription.objects.create(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("200.00"),
            investment_share=Decimal("2.00")
        )

        new_project = Project.objects.create(
            startup=self.startup,
            title="Other Project",
            funding_goal=Decimal("20000.00"),
            current_funding=Decimal("0.00"),
            category=self.category,
            email="other@example.com"
        )

        data = {
            "project": new_project.pk,
            "amount": "100.00"
        }

        serializer = SubscriptionSerializer(
            subscription,
            data={
                "project": new_project.pk,
                "investor": subscription.investor.pk,
                "amount": data.get("amount", subscription.amount)
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

        with self.assertRaises(serializers.ValidationError) as context:
            serializer.save()

        self.assertIn("project", context.exception.detail)

    def test_rounding_of_investment_share(self):
        data = {
            "investor": self.investor1.pk,
            "project": self.project.pk,
            "amount": "333.33"
        }

        serializer = SubscriptionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()
        self.assertEqual(subscription.investment_share, Decimal("3.33"))

    def test_total_investment_share_cannot_exceed_100_percent(self):
        Subscription.objects.create(
            investor=self.investor1,
            project=self.project,
            amount=Decimal("6000.00"),
            investment_share=Decimal("60.00")
        )
        Subscription.objects.create(
            investor=self.investor2,
            project=self.project,
            amount=Decimal("3000.00"),
            investment_share=Decimal("30.00")
        )

        user3 = self._create_user("inv3@example.com", "Investor", "Three")
        investor3 = Investor.objects.create(
            user=user3,
            industry=self.industry,
            location=self.location,
            company_name="Investor Three",
            email=user3.email,
            founded_year=2015,
            team_size=10,
            stage="growth",
            fund_size=Decimal("500000.00")
        )

        data = {
            "investor": investor3.pk,
            "project": self.project.pk,
            "amount": "2000.00"
        }

        serializer = SubscriptionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

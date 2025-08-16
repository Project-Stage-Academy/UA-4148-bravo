from decimal import Decimal, ROUND_DOWN
from rest_framework.test import APIRequestFactory
from common.enums import Stage
from investments.serializers.subscription_create import SubscriptionCreateSerializer
from investments.services.investment_share_service import recalculate_investment_shares, calculate_investment_share
from tests.test_base_case import BaseAPITestCase


class SubscriptionSerializerValidDataTests(BaseAPITestCase):
    def test_subscription_serializer_valid_data(self):
        data = self.get_subscription_data(self.investor1, self.project, 250.00)
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.investor1.user
        
        serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), f"Serializer validation failed: {serializer.errors}")

    def test_valid_subscription_creation(self):
        data = self.get_subscription_data(self.investor1, self.project, Decimal("250.00"))

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.investor1.user

        serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), f"Serializer validation failed: {serializer.errors}")

        subscription = serializer.save()

        recalculate_investment_shares(self.project)
        subscription.refresh_from_db()

        expected_share = calculate_investment_share(subscription.amount, self.project.funding_goal)

        self.assertAlmostEqual(float(subscription.amount), 250.00, places=2)
        self.assertAlmostEqual(float(subscription.investment_share), float(expected_share), places=2)

    def test_rounding_of_investment_share(self):
        data = self.get_subscription_data(self.investor1, self.project, 333.33)

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.investor1.user

        serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()
        
        recalculate_investment_shares(self.project)
        subscription.refresh_from_db()

        expected_share = (Decimal("333.33") / self.project.funding_goal * 100).quantize(Decimal("0.01"),
                                                                                        rounding=ROUND_DOWN)
        self.assertEqual(subscription.investment_share, expected_share)

    def test_minimum_amount_boundary(self):
        data = self.get_subscription_data(self.investor1, self.project, 0.01)

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.investor1.user

        serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()

        recalculate_investment_shares(self.project)
        subscription.refresh_from_db()

        expected_share = (Decimal("0.01") / self.project.funding_goal * 100).quantize(Decimal("0.01"))
        self.assertEqual(subscription.investment_share, expected_share)

    def test_cumulative_rounding_errors(self):
        self.project.funding_goal = Decimal("100.00")
        self.project.save()

        increments = [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
        subscriptions = []
        factory = APIRequestFactory()

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
            
            request = factory.get('/')
            request.user = investor.user

            serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
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
    def test_missing_amount_field(self):
        data = self.get_subscription_data(self.investor1, self.project, 250.00)
        data.pop("amount")

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.investor1.user

        serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        self.assertTrue(
            any("required" in str(msg).lower() for msg in serializer.errors["amount"]),
            f"Expected 'required' error message for missing amount, got: {serializer.errors['amount']}"
        )

    def test_negative_amount_is_rejected(self):
        data = self.get_subscription_data(self.investor1, self.project, -100.00)

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.investor1.user

        serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("greater than or equal to" in str(msg).lower() for msg in error_messages),
            f"Expected 'amount' error message about positive value, got: {error_messages}"
        )

    def test_zero_amount_is_rejected(self):
        data = self.get_subscription_data(self.investor1, self.project, 0.00)
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.investor1.user

        serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("greater than or equal to" in str(msg).lower() for msg in error_messages),
            f"Expected error message about amount being greater than 0, got: {error_messages}"
        )


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class SubscriptionSerializerInvestmentConstraintsTests(BaseAPITestCase):
    def test_self_investment_rejected(self):
        self.project.startup.user = self.investor1.user
        self.project.startup.save()
        data = self.get_subscription_data(self.investor1, self.project, Decimal("100.00"))
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.investor1.user
        
        serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        error_messages = serializer.errors["non_field_errors"]
        self.assertTrue(
            any("cannot invest in their own" in str(msg).lower() for msg in error_messages),
            f"Expected self-investment error, got: {error_messages}"
        )

    def test_exceeds_funding_goal(self):
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

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.investor2.user
        
        serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("exceeds funding goal" in str(msg).lower() for msg in error_messages),
            f"Expected 'exceeds funding goal' error message, got: {error_messages}"
        )

    def test_sequential_subscriptions_exceeding_funding_goal(self):
        amount1 = (self.project.funding_goal * Decimal("0.6")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        first_data = self.get_subscription_data(self.investor1, self.project, amount1)

        amount2 = (self.project.funding_goal * Decimal("0.5")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        second_data = self.get_subscription_data(self.investor2, self.project, amount2)
        
        factory = APIRequestFactory()
        request1 = factory.get('/')
        request1.user = self.investor1.user

        serializer1 = SubscriptionCreateSerializer(data=first_data, context={'request': request1})
        self.assertTrue(serializer1.is_valid(), serializer1.errors)
        serializer1.save()
        
        request2 = factory.get('/')
        request2.user = self.investor2.user
        
        serializer2 = SubscriptionCreateSerializer(data=second_data, context={'request': request2})
        self.assertFalse(serializer2.is_valid())
        self.assertIn("amount", serializer2.errors)
        error_messages = serializer2.errors["amount"]
        self.assertTrue(
            any("exceeds funding goal" in str(msg).lower() for msg in error_messages),
            f"Expected 'exceeds funding goal' error message, got: {error_messages}"
        )

    def test_fully_funded_project_no_more_subscriptions(self):
        self.get_or_create_subscription(
            investor=self.investor1,
            project=self.project,
            amount=self.project.funding_goal,
            investment_share=Decimal("100.00")
        )

        data = self.get_subscription_data(self.investor2, self.project, Decimal("1.00"))
        
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.investor2.user
        
        serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
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

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = investor3.user

        serializer = SubscriptionCreateSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)
        error_messages = serializer.errors["amount"]
        self.assertTrue(
            any("exceeds funding goal" in str(msg).lower() for msg in error_messages),
            f"Expected 'exceeds funding goal' error message, got: {error_messages}"
        )
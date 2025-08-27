from decimal import Decimal, ROUND_DOWN
from django.test import TestCase
from common.enums import Stage
from investments.serializers import (
    SubscriptionCreateSerializer,
    calculate_investment_share,
    recalculate_investment_shares,
)
from tests.setup_tests_data import TestDataMixin


class SubscriptionSerializerTests(TestDataMixin, TestCase):
    def setUp(self):
        self.setup_users()
        self.setup_investors()
        self.setup_startups()
        self.setup_projects()
        self.data = {
            "investor": str(self.investor1.id),
            "project": str(self.project1.id),
            "amount": "20000.00",
        }

    def test_valid_subscription(self):
        serializer = self.serializer_with_user(self.data, self.user1)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()
        self.assertEqual(subscription.amount, Decimal("20000.00"))
        self.assertEqual(subscription.project, self.project1)

    def test_subscription_exceeds_goal(self):
        data = self.data.copy()
        data["amount"] = "2000000.00"
        serializer = self.serializer_with_user(data, self.user1)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Investment amount exceeds the project goal", str(serializer.errors))

    def test_subscription_when_project_fully_funded(self):
        self.project1.raised_amount = self.project1.goal
        self.project1.save()
        serializer = self.serializer_with_user(self.data, self.user1)
        self.assertFalse(serializer.is_valid())
        self.assertIn("This project is already fully funded", str(serializer.errors))

    def test_self_investment_not_allowed(self):
        self.project1.startup = self.startup1
        self.project1.save()
        self.startup1.user = self.user1
        self.startup1.save()

        serializer = self.serializer_with_user(self.data, self.user1)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Startup owners cannot invest in their own projects", str(serializer.errors))

    def test_sequential_overfunding_investments(self):
        self.data["amount"] = "60000.00"
        serializer = self.serializer_with_user(self.data, self.user1)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        data2 = {
            "investor": str(self.investor2.id),
            "project": str(self.project1.id),
            "amount": "50000.00",
        }
        serializer2 = self.serializer_with_user(data2, self.user2)
        self.assertFalse(serializer2.is_valid())
        self.assertIn("Investment amount exceeds the project goal", str(serializer2.errors))

    def test_rounding_of_investment_share(self):
        self.project1.goal = Decimal("333")
        self.project1.save()

        data = self.data.copy()
        data["amount"] = "100"
        serializer = self.serializer_with_user(data, self.user1)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        subscription = serializer.save()

        expected_share = calculate_investment_share(subscription.amount, self.project1.goal)
        self.assertEqual(subscription.share, expected_share)

    def test_investment_share_calculation(self):
        subscription_amount = Decimal("25000.00")
        project_goal = Decimal("100000.00")

        expected_share = calculate_investment_share(subscription_amount, project_goal)
        self.assertEqual(expected_share, Decimal("0.25"))

    def test_investment_share_with_rounding(self):
        subscription_amount = Decimal("333.00")
        project_goal = Decimal("1000.00")

        expected_share = calculate_investment_share(subscription_amount, project_goal)
        self.assertEqual(expected_share, Decimal("0.333").quantize(Decimal("0.0001"), rounding=ROUND_DOWN))

    def test_recalculate_investment_shares(self):
        subscription1 = self.serializer_with_user(self.data, self.user1).save()

        data2 = {
            "investor": str(self.investor2.id),
            "project": str(self.project1.id),
            "amount": "10000.00",
        }
        subscription2 = self.serializer_with_user(data2, self.user2).save()

        recalculate_investment_shares(self.project1)

        self.project1.refresh_from_db()
        subscription1.refresh_from_db()
        subscription2.refresh_from_db()

        total = subscription1.amount + subscription2.amount
        self.assertAlmostEqual(subscription1.share, subscription1.amount / total)
        self.assertAlmostEqual(subscription2.share, subscription2.amount / total)

    def test_invalid_investor(self):
        data = {
            "investor": "invalid-id",
            "project": str(self.project1.id),
            "amount": "10000.00",
        }
        serializer = self.serializer_with_user(data, self.user1)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Invalid pk", str(serializer.errors.get("investor")))

    def test_invalid_project(self):
        data = {
            "investor": str(self.investor1.id),
            "project": "invalid-id",
            "amount": "10000.00",
        }
        serializer = self.serializer_with_user(data, self.user1)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Invalid pk", str(serializer.errors.get("project")))

    def test_investment_in_nonexistent_project(self):
        data = {
            "investor": str(self.investor1.id),
            "project": "00000000-0000-0000-0000-000000000000",
            "amount": "10000.00",
        }
        serializer = self.serializer_with_user(data, self.user1)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Project does not exist", str(serializer.errors.get("project")))


from decimal import Decimal
from django.db import models
from django.test.utils import override_settings
from investments.models import Subscription
from investments.services.investment_share_service import recalculate_investment_shares, calculate_investment_share
from tests.test_base_case import BaseAPITestCase


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class InvestmentShareServiceTest(BaseAPITestCase):
    """
    Test case for verifying the correct calculation of investment shares
    for subscriptions related to a project.
    """

    def test_recalculate_shares(self):
        """
        Subscriptions with amounts 100 and 300 should have shares 1.00 and 3.00,
        and total shares should be 4.00.
        """
        s1 = self.get_or_create_subscription(self.investor1, self.project, 100, 0.00)
        s2 = self.get_or_create_subscription(self.investor2, self.project, 300, 0.00)

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        s2.refresh_from_db()

        self.assertEqual(s1.investment_share * 100, 1.00)
        self.assertEqual(s2.investment_share * 100, 3.00)

        total_share = Subscription.objects.filter(project=self.project).aggregate(
            total=models.Sum('investment_share')
        )['total']
        self.assertEqual(total_share * 100, Decimal('4.00'))

    def test_no_subscriptions(self):
        """
        Recalculation on a project with no subscriptions should not raise errors.
        """
        try:
            recalculate_investment_shares(self.project)
        except Exception as e:
            self.fail(f"Recalculation failed with no subscriptions: {e}")

    def test_zero_total_amount(self):
        """
        If all amounts are zero, all investment shares should be 0.00.
        """
        s1 = self.get_or_create_subscription(self.investor1, self.project, 0.00, 0.00)
        s2 = self.get_or_create_subscription(self.investor2, self.project, 0.00, 0.00)

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        s2.refresh_from_db()

        self.assertEqual(s1.investment_share, 0.00)
        self.assertEqual(s2.investment_share, 0.00)

    def test_single_subscription_gets_100_percent(self):
        """
        A single subscription should get 100% investment share.
        """
        s1 = self.get_or_create_subscription(self.investor1, self.project, 10000.00, 0.00)

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        self.assertEqual(s1.investment_share * 100, 100.0)

    def test_investment_share_precision(self):
        """
        Shares should be calculated as a percentage of funding_goal
        and rounded to 2 decimal places.
        """
        s1 = self.get_or_create_subscription(self.investor1, self.project, Decimal("3333.33"), Decimal("0.00"))
        s2 = self.get_or_create_subscription(self.investor2, self.project, Decimal("6666.67"), Decimal("0.00"))

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        s2.refresh_from_db()

        expected_s1 = calculate_investment_share(s1.amount, self.project.funding_goal)
        expected_s2 = calculate_investment_share(s2.amount, self.project.funding_goal)

        self.assertEqual(s1.investment_share, expected_s1)
        self.assertEqual(s2.investment_share, expected_s2)




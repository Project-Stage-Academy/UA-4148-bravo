from decimal import Decimal
from django.db import models
from django.test.utils import override_settings

from investments.models import Subscription
from investments.services.investment_share_service import recalculate_investment_shares
from tests.test_setup import BaseInvestmentTestCase


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class InvestmentShareServiceTest(BaseInvestmentTestCase):
    """
    Test case for verifying the correct calculation of investment shares
    for subscriptions related to a project.
    """

    def test_recalculate_shares(self):
        """
        Subscriptions with amounts 100 and 300 should have shares 1.00 and 3.00,
        and total shares should be 4.00.
        """
        s1 = self.create_subscription(self.investor1, self.project, '100', '0.00')
        s2 = self.create_subscription(self.investor2, self.project, '300', '0.00')

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        s2.refresh_from_db()

        self.assertEqual(s1.investment_share, Decimal('1.00'))
        self.assertEqual(s2.investment_share, Decimal('3.00'))

        total_share = Subscription.objects.filter(project=self.project).aggregate(
            total=models.Sum('investment_share')
        )['total']
        self.assertEqual(total_share, Decimal('4.00'))

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
        s1 = self.create_subscription(self.investor1, self.project, '0.00', '0.00')
        s2 = self.create_subscription(self.investor2, self.project, '0.00', '0.00')

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        s2.refresh_from_db()

        self.assertEqual(s1.investment_share, Decimal('0.00'))
        self.assertEqual(s2.investment_share, Decimal('0.00'))

    def test_single_subscription_gets_100_percent(self):
        """
        A single subscription should get 100% investment share.
        """
        s1 = self.create_subscription(self.investor1, self.project, '10000.00', '0.00')

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        self.assertEqual(s1.investment_share, Decimal('100.00'))

    def test_investment_share_precision(self):
        """
        Shares should be rounded to 2 decimal places.
        """
        s1 = self.create_subscription(self.investor1, self.project, '3333.33', '0.00')
        s2 = self.create_subscription(self.investor2, self.project, '6666.67', '0.00')

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        s2.refresh_from_db()

        self.assertEqual(s1.investment_share, Decimal('33.33'))
        self.assertEqual(s2.investment_share, Decimal('66.67'))

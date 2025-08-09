from decimal import Decimal

from django.db import models
from django.test.utils import override_settings

from investments.models import Subscription
from investments.services.investment_share_service import recalculate_investment_shares
from investments.tests.test_setup import BaseInvestmentTestCase


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class InvestmentShareServiceTest(BaseInvestmentTestCase):
    """
    Test case for verifying the correct calculation of investment shares
    for subscriptions related to a project.
    """

    def test_recalculate_shares(self):
        s1 = Subscription.objects.create(project=self.project, investor=self.investor1, amount=Decimal('100'))
        s2 = Subscription.objects.create(project=self.project, investor=self.investor2, amount=Decimal('300'))

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
        Test that recalculating shares on a project with no subscriptions
        does not raise errors.
        """
        try:
            recalculate_investment_shares(self.project)
        except Exception as e:
            self.fail(f"Recalculation failed with no subscriptions: {e}")

    def test_zero_total_amount(self):
        """
        Test that when all subscriptions have zero amount,
        all investment shares are set to 0.00.
        """
        s1 = Subscription.objects.create(project=self.project, investor=self.investor1, amount=Decimal('0.00'))
        s2 = Subscription.objects.create(project=self.project, investor=self.investor2, amount=Decimal('0.00'))

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        s2.refresh_from_db()

        self.assertEqual(s1.investment_share, Decimal('0.00'))
        self.assertEqual(s2.investment_share, Decimal('0.00'))

    def test_single_subscription_gets_100_percent(self):
        """
        Test that a single subscription receives 100% investment share.
        """
        s1 = Subscription.objects.create(project=self.project, investor=self.investor1, amount=Decimal('10000.00'))

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        self.assertEqual(s1.investment_share, Decimal('100.00'))

    def test_investment_share_precision(self):
        """
        Test that share is correctly rounded to 2 decimal places.
        """
        s1 = Subscription.objects.create(project=self.project, investor=self.investor1, amount=Decimal('3333.33'))
        s2 = Subscription.objects.create(project=self.project, investor=self.investor2, amount=Decimal('6666.67'))

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        s2.refresh_from_db()

        self.assertEqual(s1.investment_share, Decimal('33.33'))
        self.assertEqual(s2.investment_share, Decimal('66.67'))

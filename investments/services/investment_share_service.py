from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from investments.models import Subscription


def recalculate_investment_shares(project):
    """
    Recalculates and updates investment_share for all Subscriptions of the given project.
    Uses bulk_update for performance.
    """
    investments = Subscription.objects.filter(project=project)
    total = investments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

    to_update = []
    for investment in investments:
        if investment.amount == 0 or total == 0:
            share = Decimal('0.00')
        else:
            share = (investment.amount / total * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        if investment.investment_share != share:
            investment.investment_share = share
            to_update.append(investment)

    if to_update:
        Subscription.objects.bulk_update(to_update, ['investment_share'])

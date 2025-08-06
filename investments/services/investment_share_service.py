from decimal import Decimal, ROUND_HALF_UP
from django.db import models


def recalculate_investment_shares(project):
    """
    Recalculates and updates the 'investment_share' field for all Subscription instances
    related to the given project.

    This function is idempotent and safe to call multiple times. It uses bulk_update
    for efficient database writes and skips updates if the calculated share hasn't changed.

    Args:
        project (Project): The project instance whose subscriptions' investment shares
                           need to be recalculated.

    Notes:
        - If the total invested amount is zero, all shares will be set to 0.00.
        - Assumes that Subscription.amount is always non-negative.
        - Designed to be used after changes to Subscription amounts, creations, or deletions.
    """
    from investments.models import Subscription

    investments = Subscription.objects.filter(project=project)
    total = investments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')

    to_update = []
    for investment in investments:
        if total == 0:
            share = Decimal('0.00')
        else:
            share = (investment.amount / total * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        if investment.investment_share != share:
            investment.investment_share = share
            to_update.append(investment)

    if to_update:
        Subscription.objects.bulk_update(to_update, ['investment_share'])

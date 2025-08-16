from decimal import Decimal, ROUND_HALF_UP


def calculate_investment_share(amount, funding_goal) -> Decimal:
    """
    Return the investment share as a percentage of the funding goal.
    """
    if funding_goal == 0:
        return Decimal("0.00")

    share = (Decimal(amount) / Decimal(funding_goal) * Decimal("100"))
    return share.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def recalculate_investment_shares(project):
    """
    Recalculates and updates the 'investment_share' field for all Subscription instances
    based on the project's funding goal.
    """
    from investments.models import Subscription

    funding_goal = project.funding_goal or Decimal("0.00")
    investments = Subscription.objects.filter(project=project)

    to_update = []
    for investment in investments:
        share = calculate_investment_share(investment.amount, funding_goal)
        if investment.investment_share != share:
            investment.investment_share = share
            to_update.append(investment)

    if to_update:
        Subscription.objects.bulk_update(to_update, ['investment_share'])

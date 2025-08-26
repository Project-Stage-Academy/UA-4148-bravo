from decimal import Decimal, ROUND_DOWN


def _to_decimal(x):
    """Helper function to safely convert values to Decimal."""
    return x if isinstance(x, Decimal) else Decimal(str(x))


def calculate_investment_share(amount, funding_goal) -> Decimal:
    """
    Calculate the investment share (in percentage) of a subscription.

    Formula:
        share = (amount / funding_goal) * 100

    - Returns 0.00 if funding_goal is 0 or less.
    - Uses ROUND_DOWN to two decimal places to match test expectations.
    - Ensures minimum share is 0.01 only when share is positive and less than 0.01.
    """
    goal = _to_decimal(funding_goal or 0)
    if goal <= 0:
        return Decimal("0.00")

    share = (_to_decimal(amount) / goal) * Decimal("100")

    # Only enforce minimum 0.01 for small positive investments
    if Decimal("0") < share < Decimal("0.01"):
        share = Decimal("0.01")

    return share.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def recalculate_investment_shares(project):
    """
    Recalculate investment_share for all subscriptions of a given project.

    Only updates subscriptions where the share value has actually changed.
    """
    from investments.models import Subscription  # local import to avoid circular dependencies

    funding_goal = _to_decimal(project.funding_goal or 0)
    if funding_goal <= 0:
        return

    to_update = []
    for subscription in Subscription.objects.filter(project=project):
        share = calculate_investment_share(subscription.amount, funding_goal)
        if subscription.investment_share != share:
            subscription.investment_share = share
            to_update.append(subscription)

    if to_update:
        Subscription.objects.bulk_update(to_update, ['investment_share'])


def update_project_investment_shares_if_needed(project):
    """
    Safe wrapper to recalculate investment shares for a project
    only if funding_goal is greater than zero.
    """
    if project.funding_goal and project.funding_goal > 0:
        recalculate_investment_shares(project)








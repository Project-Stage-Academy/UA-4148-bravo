from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from projects.models import Project


def to_decimal(value, field_name="amount"):
    """
    Convert value to Decimal or raise a ValidationError.
    """
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValidationError({field_name: _("Invalid numeric value provided.")}) from e


def get_total_subscribed(project: Project) -> Decimal:
    """
    Return the total subscribed amount for the project.
    """
    return project.subscriptions.aggregate(total=Sum('amount')).get('total') or Decimal("0")


def validate_project_funding_limit(project: Project, amount, current_subscription_amount=Decimal("0.00")) -> None:
    """
    Ensure that adding `amount` does not exceed the project's funding goal.
    """
    amount = to_decimal(amount)
    current_subscription_amount = to_decimal(current_subscription_amount)
    total_subscribed = get_total_subscribed(project) - current_subscription_amount

    if total_subscribed >= project.funding_goal or project.current_funding >= project.funding_goal:
        raise ValidationError({"project": _("Project is fully funded.")})

    if total_subscribed + amount > project.funding_goal:
        max_allowed = project.funding_goal - total_subscribed
        raise ValidationError({
            "amount": _(f"Amount exceeds funding goal. Max allowed: {max_allowed:.2f}")
        })

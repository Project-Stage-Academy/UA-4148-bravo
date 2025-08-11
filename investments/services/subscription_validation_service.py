from decimal import Decimal
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from investments.services.subscriptions import validate_project_funding_limit
from validation.validate_self_investment import validate_self_investment


def validate_subscription_business_rules(investor, project, amount, exclude_amount=Decimal('0.00')):
    """
    Runs all business-level validation rules for a subscription.
    """
    if not project:
        raise DjangoValidationError({"project": _("Project is required.")})

    if not investor:
        raise DjangoValidationError({"investor": _("Investor is required.")})

    validate_self_investment(investor, project)
    validate_project_funding_limit(project, amount, current_subscription_amount=exclude_amount)

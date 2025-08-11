from investments.models import Subscription
from decimal import Decimal
from typing import Optional, Dict, Any


class SubscriptionMixin:
    @classmethod
    def _normalize_subscription_args(
        cls,
        investor,
        project,
        amount: float,
        investment_share: Optional[float] = None
    ) -> Dict[str, Any]:
        """Internal helper to normalize subscription arguments."""
        data = {
            "investor": investor,
            "project": project,
            "amount": Decimal(amount),
        }
        if investment_share is not None:
            data["investment_share"] = Decimal(investment_share)
        return data

    @classmethod
    def create_subscription(cls, investor, project, amount, investment_share):
        """Create and return a new Subscription instance."""
        kwargs = cls._normalize_subscription_args(investor, project, amount, investment_share)
        return Subscription.objects.create(**kwargs)

    @staticmethod
    def get_subscription_data(investor, project, amount) -> dict:
        """Prepare subscription payload for API tests."""
        data = {
            "amount": str(amount)
        }
        if investor is not None:
            data["investor"] = investor.pk
        if project is not None:
            data["project"] = project.pk
        return data

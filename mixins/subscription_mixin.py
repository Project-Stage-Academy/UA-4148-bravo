from investments.models import Subscription
from decimal import Decimal
from typing import Optional, Dict, Any


class SubscriptionMixin:
    """
    Mixin class providing utility methods for creating and managing Subscription instances
    used in testing.
    """

    @classmethod
    def _normalize_subscription_args(
        cls,
        investor,
        project,
        amount: float,
        investment_share: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Internal helper to normalize subscription creation arguments.

        Args:
            investor (Investor): Investor instance for the subscription.
            project (Project): Project instance for the subscription.
            amount (float): Amount invested in the subscription.
            investment_share (Optional[float], optional): Optional investment share percentage.

        Returns:
            dict: Dictionary of normalized arguments suitable for Subscription creation.
        """
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
        """
        Create and return a new Subscription instance with the given parameters.

        Args:
            investor (Investor): Investor instance for the subscription.
            project (Project): Project instance for the subscription.
            amount (float): Amount invested.
            investment_share (Optional[float]): Investment share percentage.

        Returns:
            Subscription: Newly created Subscription instance.
        """
        kwargs = cls._normalize_subscription_args(investor, project, amount, investment_share)
        return Subscription.objects.create(**kwargs)

    @staticmethod
    def get_subscription_data(investor, project, amount) -> dict:
        """
        Prepare a dictionary payload representing a subscription, useful for API testing.

        Args:
            investor (Investor or None): Investor instance or None.
            project (Project or None): Project instance or None.
            amount (float): Amount invested.

        Returns:
            dict: Dictionary containing subscription data with IDs for investor and project.
        """
        data = {
            "amount": str(amount)
        }
        if investor is not None:
            data["investor"] = investor.pk
        if project is not None:
            data["project"] = project.pk
        return data

    @classmethod
    def tear_down(cls):
        """
        Clean up all Subscription instances created during the tests.

        If the class tracks created subscriptions in `_created_subscriptions`, deletes them from DB.
        """
        if hasattr(cls, '_created_subscriptions'):
            for subscription in cls._created_subscriptions:
                Subscription.objects.filter(pk=subscription.pk).delete()

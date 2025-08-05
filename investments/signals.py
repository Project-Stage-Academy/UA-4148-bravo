from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from investments.models import Subscription
from investments.services.investment_share_service import recalculate_investment_shares


@receiver([post_save, post_delete], sender=Subscription)
def update_investment_share(sender, instance, **kwargs):
    """
    Signal handler that triggers recalculation of investment shares
    for all subscriptions related to the project whenever a Subscription
    instance is saved or deleted.

    Args:
        sender (Model): The model class sending the signal.
        instance (Subscription): The Subscription instance that was saved or deleted.
        **kwargs: Additional keyword arguments.
    """
    recalculate_investment_shares(instance.project)

from django.db.models.signals import post_save, post_delete
from investments.tasks import recalc_investment_shares_task


def connect_signals(apps):
    """
    Connects all signal handlers for the investments app.
    Uses Celery task to avoid recalculating shares in the request thread.
    """
    Subscription = apps.get_model('investments', 'Subscription')

    def update_investment_share(sender, instance, **kwargs):
        """
        Signal handler that triggers asynchronous recalculation of investment shares
        for all subscriptions related to the project whenever a Subscription
        instance is saved or deleted.
        """
        recalc_investment_shares_task.delay(instance.project.id)

    post_save.connect(
        update_investment_share,
        sender=Subscription,
        dispatch_uid='update_investment_share_post_save'
    )
    post_delete.connect(
        update_investment_share,
        sender=Subscription,
        dispatch_uid='update_investment_share_post_delete'
    )

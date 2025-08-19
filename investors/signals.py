from django.db.models.signals import post_save
from django.dispatch import receiver
from investors.models import SavedStartup


@receiver(post_save, sender=SavedStartup)
def on_saved_startup_created(sender, instance: SavedStartup, created, **kwargs):
    """
    Signal handler triggered after a SavedStartup object is created.
    If the investor saves someone else's startup, a 'follow' notification is generated.
    """
    if not created:
        return


    from notifications.services import notify_follow

    investor = instance.investor          # Investor
    startup = instance.startup            # Startup

    if investor.user_id == startup.user_id:
        return

    notify_follow(investor, startup)

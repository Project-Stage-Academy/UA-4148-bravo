from django.apps import AppConfig

class InvestorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "investors"

    def ready(self):
        """
        Import signal handlers when the 'investors' app is ready.
        Ensures that signals (e.g., SavedStartup post_save) are connected.
        """
        from . import signals 
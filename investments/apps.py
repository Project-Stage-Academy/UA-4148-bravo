from django.apps import AppConfig

from investments import signals


class InvestmentsConfig(AppConfig):
    """
    Application configuration class for the 'investments' app.
    Registers signal handlers on app ready.
    """
    name = 'investments'

    def ready(self):
        """
        Called when the Django app registry is fully populated.
        Registers signal handlers using a lazy-loading approach.
        """
        signals.connect_signals(self.apps)

from django.apps import AppConfig


class InvestmentsConfig(AppConfig):
    """
    Application configuration class for the 'investments' app.
    This class is used to perform application-specific initialization
    such as signal registration when the app is ready.
    """
    name = 'investments'

    def ready(self):
        """
        Called when the Django app registry is fully populated.
        This method imports and registers signal handlers for the app.
        """
        import investments.signals  # noqa

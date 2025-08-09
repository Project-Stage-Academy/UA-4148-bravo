from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'
    
    def ready(self):
        """
        Import signal handlers to ensure they are registered when the app is ready.
        """
        import users.signals

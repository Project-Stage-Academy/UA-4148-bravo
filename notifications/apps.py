from django.apps import AppConfig

class NotificationsConfig(AppConfig):
    """
    App configuration for the notifications app.
    Sets default auto field and registers the app with a custom label.
    """
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"     
    label = "notifications"       
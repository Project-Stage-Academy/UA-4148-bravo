from django.apps import AppConfig

class CommunicationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "communications"
    verbose_name = "Communications"

    def ready(self):
        # важливо: імпорт реєструє ресівери сигналів
        from . import signals  # noqa: F401

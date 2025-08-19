from django.db.models.signals import post_save
from startups.models import Startup
from startups.signals import update_startup_document

class DisableSignalMixin:
    """
    Mixin to disable the `update_startup_document` signal for Startup during tests.
    Designed to be safely used with other TestCase classes without breaking MRO.
    """

    @classmethod
    def setUpClass(cls):
        cls._signal_disabled = False
        if hasattr(cls, 'disable_signal'):
            cls.disable_signal()
        super_method = getattr(super(), 'setUpClass', None)
        if super_method:
            super_method()

    @classmethod
    def tearDownClass(cls):
        super_method = getattr(super(), 'tearDownClass', None)
        if super_method:
            super_method()
        if hasattr(cls, 'enable_signal'):
            cls.enable_signal()

    @classmethod
    def disable_signal(cls):
        if not cls._signal_disabled:
            post_save.disconnect(update_startup_document, sender=Startup)
            cls._signal_disabled = True

    @classmethod
    def enable_signal(cls):
        if cls._signal_disabled:
            post_save.connect(update_startup_document, sender=Startup)
            cls._signal_disabled = False










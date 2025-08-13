from django.db.models.signals import post_save
from django.test import TestCase

from startups.models import Startup
from startups.signals import update_startup_document


class DisableSignalMixin(TestCase):
    sender = None

    @classmethod
    def disable_signal(cls):
        post_save.disconnect(update_startup_document, sender=Startup)

    @classmethod
    def enable_signal(cls):
        post_save.connect(update_startup_document, sender=Startup)

    @classmethod
    def setUpClass(cls):
        cls.disable_signal()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.enable_signal()

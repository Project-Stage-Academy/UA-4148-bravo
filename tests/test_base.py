from django.db.models.signals import post_save
from django.test import TestCase
from rest_framework.test import APIClient
from startups.models import Startup
from startups.signals import update_startup_document
from tests.input_data import TestDataMixin


class DisableSignalMixin(TestCase):
    """Mixin to disable signals during users."""
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


class BaseAPITestCase(TestDataMixin, DisableSignalMixin):
    """Generic base users case with automatic signal disabling."""

    @classmethod
    def setUpTestData(cls):
        cls.setup_all()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

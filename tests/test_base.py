from django.db.models.signals import post_save, post_delete
from django.test import TestCase
from rest_framework.test import APIClient
from investors.models import Investor
from startups.models import Startup
from startups.signals import update_startup_document, delete_startup_document
from tests.input_data import TestDataMixin
from users.models import User


class DisableSignalMixin(TestCase):
    """Mixin to disable signals during users."""
    sender = None

    @classmethod
    def disable_signal(cls):
        post_save.disconnect(update_startup_document, sender=cls.sender)
        post_delete.disconnect(delete_startup_document, sender=cls.sender)

    @classmethod
    def enable_signal(cls):
        post_save.connect(update_startup_document, sender=cls.sender)
        post_delete.connect(delete_startup_document, sender=cls.sender)

    @classmethod
    def setUpClass(cls):
        cls.disable_signal()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.enable_signal()


class DisableSignalMixinStartup(DisableSignalMixin):
    sender = Startup


class DisableSignalMixinInvestor(DisableSignalMixin):
    sender = Investor


class DisableSignalMixinUser(DisableSignalMixin):
    sender = User


class BaseAPITestCase(TestDataMixin, TestCase):
    """Generic base users case with automatic signal disabling."""

    @classmethod
    def setUpTestData(cls):
        super().tear_down()
        cls.setup_all()

    def setUp(self):
        self.client = APIClient()
        if getattr(self, "authenticate", True):
            self.client.force_authenticate(user=self.user)

    @classmethod
    def tearDownClass(cls):
        super().tear_down()

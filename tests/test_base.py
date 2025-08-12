from django.db.models.signals import post_save
from django.test import TestCase
from rest_framework.test import APIClient
from investors.models import Investor
from startups.models import Startup
from startups.signals import update_startup_document
from tests.input_data import TestDataMixin
from users.models import User


class DisableSignalMixin(TestCase):
    """Mixin to disable signals during users."""
    sender = None

    @classmethod
    def disable_signal(cls):
        post_save.disconnect(update_startup_document, sender=cls.sender)

    @classmethod
    def enable_signal(cls):
        post_save.connect(update_startup_document, sender=cls.sender)

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

    def setUp(self):
        self.tear_down()
        self.setup_all()

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        self.tear_down()

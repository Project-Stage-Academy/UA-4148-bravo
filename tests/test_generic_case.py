from django.db.models.signals import post_save
from django.test import TestCase
from rest_framework.test import APIClient
from investors.models import Investor
from mixins.investor_mixin import InvestorMixin
from mixins.project_mixin import ProjectMixin
from mixins.startup_mixin import StartupMixin
from mixins.subscription_mixin import SubscriptionMixin
from mixins.user_mixin import UserMixin
from startups.models import Startup
from startups.signals import update_startup_document
from users.models import User


class DisableSignalMixin(TestCase):
    """Mixin to disable signals during tests."""
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


class BaseAPITestCase(StartupMixin, UserMixin, InvestorMixin, ProjectMixin, SubscriptionMixin, TestCase):
    """Generic base test case with automatic signal disabling."""

    @classmethod
    def setUpTestData(cls):
        cls.setup_all()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "tear_down"):
            cls.tear_down()
        super().tearDownClass()

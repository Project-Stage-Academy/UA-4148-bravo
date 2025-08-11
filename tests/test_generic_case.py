from django.db.models.signals import post_save
from django.test import TestCase
from rest_framework.test import APIClient
from investors.models import Investor
from startups.models import Startup
from startups.signals import update_startup_document
from users.models import User


class DisableSignalMixin(TestCase):
    """Mixin to disable signals during tests."""
    sender = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_save.disconnect(update_startup_document, sender=cls.sender)

    @classmethod
    def tearDownClass(cls):
        post_save.connect(update_startup_document, sender=cls.sender)
        super().tearDownClass()


class DisableSignalMixinStartup(DisableSignalMixin):
    sender = Startup


class DisableSignalMixinInvestor(DisableSignalMixin):
    sender = Investor


class DisableSignalMixinUser(DisableSignalMixin):
    sender = User


class BaseAPITestCase(TestCase):
    """Generic base test case with automatic signal disabling."""

    @classmethod
    def setUpTestData(cls):
        cls.setup_all()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=getattr(self, "user1", None))

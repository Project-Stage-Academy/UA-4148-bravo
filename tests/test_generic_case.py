from django.test import TestCase
from rest_framework.test import APIClient
from mixins.disable_elasticsearch_mixin import DisableSignalMixin


class BaseAPITestCase(TestCase):
    """
    Generic base test case for startup/investor/etc. tests.
    Model is required in subclasses.
    """

    @classmethod
    def setup_all(cls):
        pass

    @classmethod
    def setUpTestData(cls):
        if cls.model is None:
            raise ValueError("You must define `model` in subclass")
        DisableSignalMixin(cls.model, cls.receiver).disable()
        cls.setup_all()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=getattr(self, "user1", None))

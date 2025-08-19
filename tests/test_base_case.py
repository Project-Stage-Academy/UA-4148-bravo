from rest_framework.test import APITestCase, APIClient
from tests.test_disable_signal_mixin import DisableElasticsearchSignalsMixin
from tests.setup_tests_data import TestDataMixin

class BaseAPITestCase(DisableElasticsearchSignalsMixin, TestDataMixin, APITestCase):
    """Generic base API case with automatic signal disabling and test data setup."""

    @classmethod
    def setUpClass(cls):
        # Call superclass setUpClass first (includes signal disabling)
        super().setUpClass()
        # Create all test data AFTER signals are disabled
        cls.setup_all()

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)













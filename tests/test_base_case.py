from rest_framework.test import APITestCase, APIClient
from tests.test_disable_signal_mixin import DisableSignalsMixin
from tests.setup_tests_data import TestDataMixin


class BaseAPITestCase(DisableSignalsMixin, TestDataMixin, APITestCase):
    """
    Base test case for API tests.
    - Disables Elasticsearch & Celery signals (via DisableSignalsMixin)
    - Sets up base test data (via TestDataMixin)
    - Provides authenticated API client
    """

    def setUp(self):
        """
        Creates an authenticated API client before each test.
        """
        super().setUp()
        self.client = APIClient()
        if hasattr(self, "user") and self.user:
            self.client.force_authenticate(user=self.user)
















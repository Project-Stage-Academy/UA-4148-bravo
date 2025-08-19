from rest_framework.test import APITestCase, APIClient
from tests.test_disable_signal_mixin import DisableElasticsearchSignalsMixin
from tests.setup_tests_data import TestDataMixin

class BaseAPITestCase(DisableElasticsearchSignalsMixin, TestDataMixin, APITestCase):
    """
    Base test case for API tests.
    Automatically disables Elasticsearch signals and sets up test data.
    """

    def setUp(self):
        super().setUp()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)














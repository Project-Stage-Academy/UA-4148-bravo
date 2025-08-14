from rest_framework.test import APIClient

from tests.test_disable_signal_mixin import DisableSignalMixin
from tests.setup_tests_data import TestDataMixin


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

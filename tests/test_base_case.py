from rest_framework.test import APIClient, APITestCase, APIRequestFactory
from investments.serializers.subscription_create import SubscriptionCreateSerializer
from tests.test_disable_signal_mixin import DisableSignalsMixin, DisableSignalMixin
from tests.setup_tests_data import TestDataMixin


class BaseAPITestCase(TestDataMixin, DisableSignalsMixin, APITestCase):
    """
    Base test case for API tests.
    - Disables Elasticsearch & Celery signals (via DisableSignalsMixin)
    - Sets up base test data (via TestDataMixin)
    - Provides authenticated API client
    """

    @classmethod
    def setUpTestData(cls):
        cls.setup_all()

    def setUp(self):
        """
        Creates an authenticated API client before each test.
        """
        super().setUp()
        self.client = APIClient()
        if hasattr(self, "user") and self.user:
            self.client.force_authenticate(user=self.user)

    def serializer_with_user(self, data, user, **extra_context):
        """
        Helper to instantiate a serializer with a request context containing the given user.
        """
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        context = {'request': request, **extra_context}
        return SubscriptionCreateSerializer(data=data, context=context)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()


class BaseCompanyCreateAPITestCase(TestDataMixin, DisableSignalsMixin, APITestCase):
    """
    Base test case for company creation tests.
    Sets up users and basic dependencies but does NOT create default startups/investors,
    ensuring a clean slate for creation tests.
    """

    @classmethod
    def setUpTestData(cls):
        """Setup only the necessary prerequisite data."""
        cls.setup_users()
        cls.setup_industries()
        cls.setup_locations()

    def setUp(self):
        self.client = APIClient()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

from rest_framework.test import APIClient, APITestCase, APIRequestFactory
from investments.serializers.subscription_create import SubscriptionCreateSerializer

from tests.test_disable_signal_mixin import DisableSignalMixin
from tests.setup_tests_data import TestDataMixin


class BaseAPITestCase(TestDataMixin, DisableSignalMixin, APITestCase):
    """Generic base users case with automatic signal disabling."""

    @classmethod
    def setUpTestData(cls):
        cls.setup_all()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def serializer_with_user(self, data, user, **extra_context):
        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = user
        project = extra_context.get('project', getattr(self, "project", None))
        if not project:
            raise ValueError("Project must be passed to serializer_with_user via extra_context or as self.project.")
        # if 'project' not in data:
        #     data = data.copy()
        #     data['project'] = project.id
        context = {'request': request, 'project': project, **extra_context}
        return SubscriptionCreateSerializer(data=data, context=context)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

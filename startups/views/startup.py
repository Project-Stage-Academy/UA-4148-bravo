from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from startups.models import Startup
from startups.serializers.startup_full import StartupSerializer
from startups.serializers.startup_create import StartupCreateSerializer
from startups.views.startup_base import BaseValidatedModelViewSet
from users.permissions import CanCreateCompanyPermission

class StartupViewSet(BaseValidatedModelViewSet):
    queryset = Startup.objects.select_related('user', 'industry', 'location') \
        .prefetch_related('projects')
    
    serializer_class = StartupSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['industry', 'stage', 'location__country']
    search_fields = ['company_name', 'user__first_name', 'user__last_name', 'email']

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateCompanyPermission()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the request action.
        """
        if self.action == 'create':
            return StartupCreateSerializer
        return StartupSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from startups.models import Startup
from startups.serializers.startup_full import StartupSerializer
from startups.views.startup_base import BaseValidatedModelViewSet
from users.permissions import IsStartupUser


class StartupViewSet(BaseValidatedModelViewSet):
    queryset = Startup.objects.select_related('user', 'industry', 'location') \
        .prefetch_related('projects')
    serializer_class = StartupSerializer
    permission_classes = [IsAuthenticated, IsStartupUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['industry', 'stage', 'location__country']
    search_fields = ['company_name', 'user__first_name', 'user__last_name', 'email']

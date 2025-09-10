from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from startups.models import Startup
from startups.serializers.startup_list import StartupListSerializer
from startups.serializers.startup_detail import StartupDetailSerializer
from startups.filters import StartupFilter
from startups.serializers.startup_create import StartupCreateSerializer
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from startups.serializers.startup_list import StartupListSerializer
from startups.serializers.startup_detail import StartupDetailSerializer
from django_filters.rest_framework import DjangoFilterBackend
from users.cookie_jwt import CookieJWTAuthentication
from .startup import StartupFilterSet

class StartupCatalogViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = StartupFilterSet
    search_fields = ['company_name','description']
    ordering_fields = ['company_name','team_size','funding_needed','created_at']
    ordering = ['company_name']
    lookup_field = 'id'
    authentication_classes = [CookieJWTAuthentication]

    def get_queryset(self):
        user = self.request.user
        base = (Startup.objects
                .select_related('industry','location','user')
                .prefetch_related('projects'))
        public = base.filter(is_public=True)
        return (public | base.filter(user=user)).distinct()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StartupListSerializer
        if self.action == 'retrieve':
            return StartupDetailSerializer
        if self.action == 'create':
            return StartupCreateSerializer
        return StartupDetailSerializer
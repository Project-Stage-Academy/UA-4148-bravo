import logging
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    OrderingFilterBackend,
    SearchFilterBackend,
)
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from elasticsearch.exceptions import ConnectionError, TransportError, NotFoundError
from rest_framework import status
from rest_framework.response import Response
from startups.documents import StartupDocument
from startups.serializers.startup_elasticsearch import StartupDocumentSerializer
from users.cookie_jwt import CookieJWTAuthentication
from users.permissions import IsAuthenticatedOr401
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend, OrderingFilterBackend, CompoundSearchFilterBackend
)
from elasticsearch_dsl import Q as ES_Q

logger = logging.getLogger(__name__)


class StartupDocumentView(DocumentViewSet):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedOr401]
    document = StartupDocument
    serializer_class = StartupDocumentSerializer
    lookup_field = 'id'

    filter_backends = [FilteringFilterBackend, OrderingFilterBackend, CompoundSearchFilterBackend]


    filter_fields = {
        'company_name': 'company_name.raw',
        'stage': 'stage.raw',                
        'location.country': 'llocation.country.raw', 
        'country': 'location.country.raw',      
        'industries.name': 'industries.name.raw',
    }

    ordering_fields = {
        'company_name': 'company_name.raw',
        'stage': 'stage.raw',
        'location.country': 'location.country.raw',
    }

    ordering = ('-stage',)

    search_fields = (
        'company_name',
        'description',
    )
    
    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        should = [ES_Q('term', is_public=True)]
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            should.append(ES_Q('term', user_id=user.id))
        return queryset.query('bool', should=should, minimum_should_match=1)

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except (ConnectionError, TransportError, NotFoundError):
            return Response(
                {"detail": "Search service is temporarily unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

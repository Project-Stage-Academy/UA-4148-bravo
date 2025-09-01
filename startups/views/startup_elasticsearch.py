import logging
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    OrderingFilterBackend,
    SearchFilterBackend,
)
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from elasticsearch.exceptions import ConnectionError, TransportError
from rest_framework import status
from rest_framework.response import Response
from startups.documents import StartupDocument
from startups.serializers.startup_elasticsearch import StartupDocumentSerializer
from users.cookie_jwt import CookieJWTAuthentication
from users.permissions import IsAuthenticatedOr401

logger = logging.getLogger(__name__)


class StartupDocumentView(DocumentViewSet):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedOr401]
    document = StartupDocument
    serializer_class = StartupDocumentSerializer
    lookup_field = 'id'

    filter_backends = [
        FilteringFilterBackend,
        OrderingFilterBackend,
        SearchFilterBackend,
    ]

    filter_fields = {
        'company_name': 'company_name.raw',
        'stage': 'stage',
        'location.country': 'location.country',
        'industries.name': 'industries.name',
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

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except (ConnectionError, TransportError) as e:
            return Response(
                {"detail": "Search service is temporarily unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

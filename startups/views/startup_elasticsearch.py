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

logger = logging.getLogger(__name__)


class StartupDocumentView(DocumentViewSet):
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
        'funding_stage': 'funding_stage',
        'location.country': 'location.country',
        'industry.name': 'industry.name',
        'investment_needs': 'investment_needs',
        'company_size': 'company_size',
        'is_active': 'is_active',
    }

    ordering_fields = {
        'company_name': 'company_name.raw',
        'stage': 'stage.raw',
        'funding_stage': 'funding_stage.raw',
        'location.country': 'location.country.raw',
        'company_size': 'company_size',
        'created_at': 'created_at',
    }

    ordering = ('-stage',)

    search_fields = (
        'company_name',
        'description',
        'investment_needs',
    )

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except (ConnectionError, TransportError):
            return Response(
                {"detail": "Search service is temporarily unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from elasticsearch.exceptions import ConnectionError, TransportError
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    OrderingFilterBackend,
    SearchFilterBackend,
)
from .documents import StartupDocument
from .serializers import StartupDocumentSerializer


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
        'funding_stage': 'funding_stage',
        'location.country': 'location.country',
        'industries.name': 'industries.name',
    }

    ordering_fields = {
        'company_name': 'company_name.raw',
        'funding_stage': 'funding_stage.raw',
        'location.country': 'location.country.raw',
    }
    
    ordering = ('-funding_stage',)

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
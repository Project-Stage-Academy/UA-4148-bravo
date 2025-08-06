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
from .documents import ProjectDocument
from .serializers import ProjectDocumentSerializer


class ProjectDocumentView(DocumentViewSet):
    document = ProjectDocument
    serializer_class = ProjectDocumentSerializer

    filter_backends = [
        FilteringFilterBackend,
        OrderingFilterBackend,
        SearchFilterBackend,
    ]

    filter_fields = {
        'title': 'title.raw',
        'category.name': 'category.name',
        'startup.company_name': 'startup.company_name',
    }

    ordering_fields = {
        'id': 'id',
        'title': 'title.raw',
    }

    search_fields = (
        'title',
        'description',
        'goals',
    )

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except (ConnectionError, TransportError) as e:
            return Response(
                {"detail": "Search service is temporarily unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
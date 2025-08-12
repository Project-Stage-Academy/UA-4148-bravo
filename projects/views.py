from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from elasticsearch.exceptions import ConnectionError, TransportError
from elasticsearch_dsl import Q
from .models import Project
from .serializers import ProjectSerializer

from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    OrderingFilterBackend,
    SearchFilterBackend,
)
from .documents import ProjectDocument
from .permissions import IsOwnerOrReadOnly
from .serializers import ProjectDocumentSerializer
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing projects.
    Optimized to avoid N+1 queries with select_related.
    """
    queryset = Project.objects.select_related('startup', 'category').all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'category', 'startup']
    search_fields = ['title', 'description', 'email']
    ordering_fields = ['created_at', 'funding_goal', 'current_funding']
    ordering = ['-created_at']


class ProjectDocumentView(DocumentViewSet):
    """
    API endpoint for searching projects using Elasticsearch.
    Handles ES downtime gracefully.
    """
    document = ProjectDocument
    serializer_class = ProjectDocumentSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        FilteringFilterBackend,
        OrderingFilterBackend,
        SearchFilterBackend,
    ]

    filter_fields = {
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
    )

    def filter_queryset(self, queryset):
        params = self.request.query_params
        allowed_params = set(self.filter_fields.keys()) | {'search'}

        for param in params.keys():
            if param not in allowed_params:
                raise ValidationError({'error': f'Invalid filter field: {param}'})

        must_queries = []
        for field, es_field in self.filter_fields.items():
            if field in params:
                must_queries.append(Q('term', **{es_field: params[field]}))

        if must_queries:
            queryset = queryset.query(Q('bool', must=must_queries))

        return super().filter_queryset(queryset)

    def list(self, request, *args, **kwargs):
        allowed_fields = set(self.filter_fields.keys()) | {'search'}
        for param in request.query_params.keys():
            if param not in allowed_fields:
                return Response(
                    {'error': f'Invalid filter field: {param}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        try:
            return super().list(request, *args, **kwargs)
        except (ConnectionError, TransportError) as e:
            logger.error("Elasticsearch connection error: %s", e)
            return Response(
                {"detail": "Search service is temporarily unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

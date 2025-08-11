from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from elasticsearch.exceptions import ConnectionError, TransportError
from elasticsearch_dsl import Q
from projects.models import Project
from rest_framework.exceptions import ValidationError
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    OrderingFilterBackend,
    SearchFilterBackend,
)
from .documents import ProjectDocument
from .permissions import IsOwnerOrReadOnly
from .serializers import ProjectDocumentSerializer, ProjectReadSerializer
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing projects.
    Optimized to avoid N+1 queries by using select_related.
    Supports filtering by status, category, startup; searching by title, description, email;
    and ordering by created_at, funding_goal, and current_funding.
    """
    queryset = Project.objects.select_related('startup', 'category').all()
    serializer_class = ProjectReadSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'category', 'startup']
    search_fields = ['title', 'description', 'email']
    ordering_fields = ['created_at', 'funding_goal', 'current_funding']
    ordering = ['-created_at']


class ProjectDocumentView(DocumentViewSet):
    """
    Elasticsearch-backed viewset for Project documents.
    Supports filtering, ordering, and full-text search with robust error handling.
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
        """
        Filters the queryset based on query parameters.
        Supports multiple values per filter field and partial matches for text fields.
        Raises ValidationError if invalid filter parameters are provided.
        """
        params = self.request.query_params
        allowed_params = set(self.filter_fields.keys()) | {'search'}

        invalid_params = set(params.keys()) - allowed_params
        if invalid_params:
            allowed = ', '.join(sorted(allowed_params))
            logger.warning(f"Invalid filter field(s) attempted: {sorted(invalid_params)}. Allowed fields: {allowed}")
            raise ValidationError({
                'error': f'Invalid filter field(s): {", ".join(sorted(invalid_params))}. Allowed fields: {allowed}'
            })

        must_queries = []

        for field, es_field in self.filter_fields.items():
            if field in params:
                values = params.getlist(field)
                if field in ['title', 'description']:
                    for val in values:
                        must_queries.append(Q('wildcard', **{es_field: f'*{val}*'}))
                else:
                    for val in values:
                        must_queries.append(Q('term', **{es_field: val}))

        search_terms = params.getlist('search')
        if search_terms:
            should_queries = []
            for term in search_terms:
                should_queries.append(Q('match', title=term))
                should_queries.append(Q('match', description=term))
            if should_queries:
                must_queries.append(Q('bool', should=should_queries, minimum_should_match=1))

        if must_queries:
            queryset = queryset.query(Q('bool', must=must_queries))

        return super().filter_queryset(queryset)

    def list(self, request, *args, **kwargs):
        """
        Overrides the list action.
        Relies on filter_queryset to validate query params and filter the queryset.
        Handles Elasticsearch connection errors gracefully with HTTP 503 response.
        """
        try:
            return super().list(request, *args, **kwargs)
        except ValidationError as ve:
            logger.warning(f"Validation error on filter params: {ve.detail}")
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        except (ConnectionError, TransportError) as e:
            logger.error("Elasticsearch connection error: %s", e)
            return Response(
                {"detail": "Search service is temporarily unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

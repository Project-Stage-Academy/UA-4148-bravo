from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from elasticsearch.exceptions import ConnectionError, TransportError
from elasticsearch_dsl import Q
from projects.models import Project

from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    OrderingFilterBackend,
    SearchFilterBackend,
)

from users.cookie_jwt import CookieJWTAuthentication
from users.permissions import IsAuthenticatedOr401, HasActiveCompanyAccount
from projects.documents import ProjectDocument
from projects.permissions import IsOwnerOrReadOnly
from projects.serializers import ProjectDocumentSerializer, ProjectReadSerializer, ProjectWriteSerializer
import logging

logger = logging.getLogger(__name__)

class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing projects.

    This ViewSet supports both read and write operations for projects.
    It optimizes database access by using `select_related` for related fields
    (`startup` and `category`) to avoid N+1 query issues.

    Features:
        - Read operations: list and retrieve project details.
        - Write operations: create, update, partially update, and delete projects.
        - Filtering: by `status`, `category`, and `startup`.
        - Searching: by `title`, `description`, and `email`.
        - Ordering: by `created_at`, `funding_goal`, and `current_funding`.
        - Default ordering: newest projects first (`-created_at`).

    Permissions:
        - Authenticated users can view all projects.
        - Only the owner can modify or delete their projects.
    """
    queryset = Project.objects.select_related('startup', 'category').all()
    permission_classes = [IsAuthenticatedOr401, IsOwnerOrReadOnly, HasActiveCompanyAccount]
    authentication_classes = [CookieJWTAuthentication]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'category', 'startup']
    search_fields = ['title', 'description', 'email']
    ordering_fields = ['created_at', 'funding_goal', 'current_funding']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """
        Return the appropriate serializer class depending on the action.

        - For read actions (`list`, `retrieve`), use `ProjectReadSerializer`
          to include detailed, read-only fields.
        - For write actions (`create`), use `ProjectWriteSerializer` to handle validation and input data.
        - For the `update_project` action, we'll use `ProjectReadSerializer` for the response.
        """
        if self.action in ['list', 'retrieve', 'update_project']:
            return ProjectReadSerializer
        return ProjectWriteSerializer
    
    def perform_update(self, serializer):
        """
        Updates the project instance and sets the last editor.
        """
        serializer.instance._last_editor = self.request.user
        serializer.save()

    @action(detail=True, methods=['post'], url_path='update')
    def update_project(self, request, pk=None):
        """
        Custom action to handle project updates via a POST request.
        The URL will be /api/v1/projects/{pk}/update/
        """
        project = self.get_object()
        self.check_object_permissions(request, project)

        if 'startup_id' in request.data:
            return Response(
                {"detail": "Cannot change the startup of a project."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        serializer = ProjectWriteSerializer(project, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(ProjectReadSerializer(project).data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, *args, **kwargs):
        """
        This method will no longer be the primary way to update a project.
        The new update workflow uses a POST request to a custom endpoint.
        """
        return super().partial_update(request, *args, **kwargs)


class ProjectDocumentView(DocumentViewSet):
    """
    Elasticsearch-backed viewset for Project documents.
    Supports filtering, ordering, and full-text search with robust error handling.
    """
    permission_classes = [IsAuthenticatedOr401]
    authentication_classes = [CookieJWTAuthentication]
    document = ProjectDocument
    serializer_class = ProjectDocumentSerializer

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

from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from elasticsearch.exceptions import ConnectionError, TransportError

from .models import Project, Subscription
from .serializers import ProjectSerializer, SubscriptionCreateSerializer
from users.permissions import IsInvestor

from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    OrderingFilterBackend,
    SearchFilterBackend,
)
from .documents import ProjectDocument
from .serializers import ProjectDocumentSerializer

import logging
logger = logging.getLogger(__name__)

class SubscriptionCreateView(CreateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionCreateSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def perform_create(self, serializer):
        subscription = serializer.save(investor=self.request.user)
        project = subscription.project
        remaining_funding = project.funding_goal - project.current_funding

        message = "Subscription created successfully."
        project_status = "Fully funded" if remaining_funding <= 0 else "Partially funded"

        return Response(
            {
                "message": message,
                "remaining_funding": remaining_funding,
                "project_status": project_status
            },
            status=status.HTTP_201_CREATED
        )

class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing projects.
    Optimized to avoid N+1 queries by using select_related.
    Includes filtering, searching, and ordering.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'category', 'startup']
    search_fields = ['title', 'description', 'email']
    ordering_fields = ['created_at', 'funding_goal', 'current_funding']
    ordering = ['-created_at']


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
        'startup_name': 'startup_name',
        'status': 'status',
    }

    ordering_fields = {
        'id': 'id',
        'title': 'title.raw',
    }

    search_fields = (
        'title',
        'description',
    )

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except (ConnectionError, TransportError) as e:
            logger.error("Elasticsearch connection error: %s", e)
            return Response(
                {"detail": "Search service is temporarily unavailable. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'category', 'startup']
    search_fields = ['title', 'description', 'email']
    ordering_fields = ['created_at', 'funding_goal', 'current_funding']
    ordering = ['-created_at']

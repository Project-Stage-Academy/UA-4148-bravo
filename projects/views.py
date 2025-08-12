from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from django_filters.rest_framework import DjangoFilterBackend
from elasticsearch.exceptions import ConnectionError, TransportError
from django.db import transaction
from django.db.models import F

from .models import Project
from investments.models import Subscription
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
    """
    API endpoint to handle the creation of new investment subscriptions.
    Uses transaction management and F() expressions for safe concurrent updates.
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionCreateSerializer
    permission_classes = [IsInvestor]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                subscription = serializer.save()
                project_id = subscription.project_id

                Project.objects.filter(id=project_id).update(
                    current_funding=F('current_funding') + subscription.amount
                )

                project = Project.objects.select_related('startup', 'category').get(id=project_id)
                remaining_funding = project.funding_goal - project.current_funding
                project_status = "Fully funded" if remaining_funding <= 0 else "Partially funded"

                logger.info(f"Subscription {subscription.id} created successfully for project {project.id} by user {request.user.id}")

                return Response(
                    {
                        "message": "Subscription created successfully.",
                        "remaining_funding": remaining_funding,
                        "project_status": project_status
                    },
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            logger.error(f"Failed to create subscription for user {request.user.id}: {e}")
            return Response(
                {"detail": "Failed to create subscription. Please try again."},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing projects.
    Optimized to avoid N+1 queries with select_related.
    """
    queryset = Project.objects.select_related('startup', 'category').all()
    serializer_class = ProjectSerializer
    permission_classes = [IsInvestor]

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
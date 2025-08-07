from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from projects.models import Project
from projects.serializers import ProjectSerializer

import logging
logger = logging.getLogger(__name__)

class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for viewing and editing projects.
    Optimized to avoid N+1 queries by using select_related.
    Includes filtering, searching, and ordering.
    """
    queryset = Project.objects.select_related('startup', 'category').all()
    serializer_class = ProjectSerializer

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'category', 'startup']
    search_fields = ['title', 'description', 'email']
    ordering_fields = ['created_at', 'funding_goal', 'current_funding']
    ordering = ['-created_at']


from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    CompoundSearchFilterBackend,
    SuggesterFilterBackend,
    OrderingFilterBackend,
)
from projects.documents import ProjectDocument
from projects.serializers import ProjectDocumentSerializer
from rest_framework import generics
from projects.models import Project

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProjectSearchViewSet(DocumentViewSet):
    document = ProjectDocument
    serializer_class = ProjectDocumentSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        FilteringFilterBackend,
        CompoundSearchFilterBackend,
        SuggesterFilterBackend,
        OrderingFilterBackend,
    ]
    search_fields = ('title', 'description', 'startup_name')
    filter_fields = {
        'status': 'status.raw',
        'required_amount': 'required_amount',
        'startup_name': 'startup_name.raw',
    }
    suggester_fields = {
        'title': {
            'field': 'title.suggest',
            'suggester_type': 'completion',
            'default_analyzer': 'simple',
        },
    }
    ordering_fields = {
        'title': 'title.raw',
        'status': 'status.raw',
        'required_amount': 'required_amount',
        'startup_name': 'startup_name.raw',
    }

class ProjectView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Project.objects.all()
    serializer_class = ProjectDocumentSerializer

class PopularProjectsView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProjectDocumentSerializer

    def get_queryset(self):
        return Project.objects.order_by('-required_amount')[:10]
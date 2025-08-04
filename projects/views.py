from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    CompoundSearchFilterBackend,
)
from projects.documents import ProjectDocument
from projects.serializers import ProjectDocumentSerializer


class ProjectSearchViewSet(DocumentViewSet):
    document = ProjectDocument
    serializer_class = ProjectDocumentSerializer
    filter_backends = [FilteringFilterBackend, CompoundSearchFilterBackend]
    search_fields = ("title", "description")
    filter_fields = {
        "status": "status.raw",
        "required_amount": "required_amount",
    }
    ordering_fields = {
        "title": "title.raw",
        "status": "status.raw",
    }

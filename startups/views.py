# startups/views.py
from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from startups.documents import StartupDocument
from startups.serializers import StartupDocumentSerializer
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    CompoundSearchFilterBackend,
)

class StartupSearchViewSet(DocumentViewSet):
    document = StartupDocument
    serializer_class = StartupDocumentSerializer
    filter_backends = [FilteringFilterBackend, CompoundSearchFilterBackend]
    search_fields = ("company_name", "description")
    filter_fields = {
        "location": "location.raw",
        "funding_stage": "funding_stage.raw",
    }
    ordering_fields = {
        "company_name": "company_name.raw",
    }

from django_elasticsearch_dsl_drf.viewsets import DocumentViewSet
from .documents import StartupDocument
from .serializers import StartupDocumentSerializer
from django_elasticsearch_dsl_drf.filter_backends import (
    FilteringFilterBackend,
    OrderingFilterBackend,
    CompoundSearchFilterBackend,
)

class StartupSearchViewSet(DocumentViewSet):
    document = StartupDocument
    serializer_class = StartupDocumentSerializer
    filter_backends = [
        FilteringFilterBackend,
        OrderingFilterBackend,
        CompoundSearchFilterBackend,
    ]
    search_fields = ('company_name', 'description')
    filter_fields = {
        'funding_stage': 'exact',
        'location': 'exact',
    }
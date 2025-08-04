from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from .documents import StartupDocument

class StartupDocumentSerializer(DocumentSerializer):
    class Meta:
        document = StartupDocument
        fields = (
            "company_name",
            "description",
            "funding_stage",
            "location",
            "industries",
        )

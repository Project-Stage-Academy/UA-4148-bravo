from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from .documents import ProjectDocument

class ProjectDocumentSerializer(DocumentSerializer):
    class Meta:
        document = ProjectDocument
        fields = (
            "title",
            "description",
            "status",
            "required_amount",
        )

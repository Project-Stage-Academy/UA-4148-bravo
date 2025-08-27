from rest_framework import serializers
from startups.documents import StartupDocument
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer


class StartupDocumentSerializer(DocumentSerializer):
    """
    Serializer for StartupDocument (Elasticsearch).
    """
    industry = serializers.SerializerMethodField()

    class Meta:
        document = StartupDocument
        fields = ('id', 'company_name', 'description', 'location', 'stage', 'industry')

    def get_industry(self, obj):
        return obj.industry.name if obj.industry else None

from rest_framework import serializers
from startups.documents import StartupDocument
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer


class StartupDocumentSerializer(DocumentSerializer):
    """
    Serializer for StartupDocument (Elasticsearch).
    Includes extended fields to match full Startup data requirements.
    """
    industry = serializers.SerializerMethodField()

    class Meta:
        document = StartupDocument
        fields = (
            'id',
            'company_name',
            'description',
            'website',
            'email',
            'founded_year',
            'team_size',
            'stage',
            'industry',
            'location',
            'created_at',
            'updated_at'
        )

    def get_industry(self, obj):
        return obj.industry.name if obj.industry else None

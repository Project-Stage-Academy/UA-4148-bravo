from rest_framework import serializers
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from startups.documents import StartupDocument

class StartupDocumentSerializer(DocumentSerializer):
    industries = serializers.SerializerMethodField()

    class Meta:
        document = StartupDocument
        fields = ('id', 'company_name', 'description', 'location', 'funding_stage', 'industries')

    def get_industries(self, obj):
        if obj.industries:
            return [industry.name for industry in obj.industries]
        return []
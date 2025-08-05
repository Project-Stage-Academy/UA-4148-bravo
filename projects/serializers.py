from rest_framework import serializers
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from projects.documents import ProjectDocument

class ProjectDocumentSerializer(DocumentSerializer):
    class Meta:
        document = ProjectDocument
        fields = ('id', 'title', 'description', 'status', 'startup_name', 'required_amount')
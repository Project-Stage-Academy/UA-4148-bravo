from rest_framework import serializers
from .documents import ProjectDocument

class ProjectDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDocument
        fields = '__all__'
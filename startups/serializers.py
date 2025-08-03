from rest_framework import serializers
from .documents import StartupDocument

class StartupDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartupDocument
        fields = '__all__'
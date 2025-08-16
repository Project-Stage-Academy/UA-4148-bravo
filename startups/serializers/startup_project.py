from rest_framework import serializers
from startups.models import Startup


class StartupProjectSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for startup details.
    Intended for embedding startup data into related project views.
    """
    class Meta:
        model = Startup
        fields = ['id', 'company_name', 'stage', 'website']
        read_only_fields = fields

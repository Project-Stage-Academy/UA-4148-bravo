from rest_framework import serializers
from startups.models import Startup


class StartupProjectSerializer(serializers.ModelSerializer):
    """Read-only serializer for startup details."""

    class Meta:
        model = Startup
        fields = ['id', 'company_name', 'stage', 'website']
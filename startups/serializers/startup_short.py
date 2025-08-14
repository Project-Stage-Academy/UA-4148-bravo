from rest_framework import serializers
from startups.models import Startup


class StartupShortSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for nested use (e.g., inside Investor).
    """
    class Meta:
        model = Startup
        fields = ['id', 'company_name', 'industry', 'location', 'website', 'stage']
        read_only_fields = fields

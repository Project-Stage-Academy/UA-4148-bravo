from rest_framework import serializers
from startups.models import Startup

class StartupDetailSerializer(serializers.ModelSerializer):
    industry = serializers.CharField(source="industry.name", read_only=True)
    location = serializers.SerializerMethodField()

    class Meta:
        model = Startup
        fields = [
            "id", "company_name", "description", "industry", "stage",
            "team_size", "funding_needed", "is_verified", "location",
        ]
        read_only_fields = fields

    def get_location(self, obj):
        if obj.location_id:
            return {"country": obj.location.country, "city": obj.location.city}
        return None

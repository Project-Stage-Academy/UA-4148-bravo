from rest_framework import serializers
from investors.models import ViewedStartup

class ViewedStartupSerializer(serializers.ModelSerializer):
    startup_id = serializers.IntegerField(source="startup.id", read_only=True)
    company_name = serializers.CharField(source="startup.company_name", read_only=True)

    class Meta:
        model = ViewedStartup
        fields = ["startup_id", "company_name", "viewed_at"]
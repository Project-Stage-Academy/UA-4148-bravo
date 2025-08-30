from rest_framework import serializers
from startups.models import Startup
from projects.models import Project


class StartupSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Startup
        fields = ["id", "company_name", "stage"]


class ProjectSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "title", "status", "funding_goal"]


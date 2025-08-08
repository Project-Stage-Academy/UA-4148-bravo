from rest_framework import serializers
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from startups.documents import StartupDocument
from startups.models import Startup, Industry, Location
from projects.models import Project
from common.enums import ProjectStatus


class LocationSerializer(serializers.ModelSerializer):
    """
    Serializer for Location model.
    """
    class Meta:
        model = Location
        fields = ['id', 'country']


class IndustrySerializer(serializers.ModelSerializer):
    """
    Serializer for Industry model.
    """
    class Meta:
        model = Industry
        fields = ['id', 'name']


class StartupDocumentSerializer(DocumentSerializer):
    """
    Serializer for Elasticsearch-backed search results.
    Used by the DocumentViewSet for search responses.
    """
    industries = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta:
        document = StartupDocument
        fields = (
            'id', 'company_name', 'description', 'location',
            'funding_stage', 'industries',
            'investment_needs', 'company_size', 'is_active'
        )

    def get_industries(self, obj):
        try:
            return [i.name for i in obj.industries.all()]
        except Exception:
            try:
                return [i.get('name') for i in obj.industries]
            except Exception:
                return []

    def get_location(self, obj):
        try:
            loc = obj.location
            return {'id': loc.id, 'country': loc.country} if loc else None
        except Exception:
            return None


class ProjectNestedSerializer(serializers.ModelSerializer):
    """
    Lightweight nested serializer for including projects inside Startup detail.
    Avoids circular imports by not using full ProjectSerializer.
    """
    category = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'status', 'status_display',
            'duration', 'funding_goal', 'current_funding',
            'category', 'website', 'email', 'has_patents', 'is_participant',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_category(self, obj):
        cat = getattr(obj, 'category', None)
        if cat:
            return {'id': cat.id, 'name': getattr(cat, 'name', None)}
        return None

    def get_status_display(self, obj):
        try:
            return ProjectStatus(obj.status).label if obj.status else None
        except Exception:
            return obj.status


class StartupDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for Startup detail view (DB-based).
    Includes industries, location, and nested projects.
    """
    industries = IndustrySerializer(many=True, read_only=True)
    location = LocationSerializer(read_only=True)
    projects = ProjectNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Startup
        fields = [
            'id', 'company_name', 'description', 'location',
            'funding_stage', 'industries', 'logo', 'website',
            'investment_needs', 'company_size', 'is_active',
            'created_at', 'updated_at', 'projects'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'projects']


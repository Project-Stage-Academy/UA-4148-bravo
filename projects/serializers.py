from decimal import Decimal
from django.db import transaction
from django.db.models import F
from rest_framework import serializers
from projects.models import Project, Category
from startups.models import Startup
from common.enums import ProjectStatus
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from projects.documents import ProjectDocument
from startups.serializers.startup_project import StartupProjectSerializer
from utils.get_field_value import get_field_value

from investments.models import Subscription


class CategorySerializer(serializers.ModelSerializer):
    """Read-only serializer for category details."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class ProjectReadSerializer(serializers.ModelSerializer):
    """
    Serializer for reading Project with nested related objects,
    including custom fields for startup details.
    """
    id = serializers.IntegerField(read_only=True)
    category = CategorySerializer(read_only=True)
    startup = StartupProjectSerializer(read_only=True)
    status_display = serializers.SerializerMethodField()
    startup_name = serializers.SerializerMethodField()
    startup_logo = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'startup', 'startup_name', 'startup_logo', 'title', 'description',
            'business_plan', 'media_files', 'status', 'status_display', 'duration',
            'funding_goal', 'current_funding', 'category', 'website', 'email',
            'has_patents', 'is_participant', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_status_display(self, obj):
        return ProjectStatus(obj.status).label if obj.status else None

    def get_startup_name(self, obj):
        """Returns the name of the associated startup."""
        return obj.startup.company_name if obj.startup else None

    def get_startup_logo(self, obj):
        """Returns the URL of the startup's logo."""
        request = self.context.get('request')
        if obj.startup and obj.startup.logo:
            return request.build_absolute_uri(obj.startup.logo.url)
        return None


class ProjectWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating Project with validation.
    Ensures required fields match the model and cross-field rules are enforced.
    """
    id = serializers.IntegerField(read_only=True)
    startup_id = serializers.PrimaryKeyRelatedField(
        queryset=Startup.objects.all(),
        source='startup'
    )
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category'
    )

    funding_goal = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        required=True
    )
    current_funding = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        required=False
    )

    class Meta:
        model = Project
        fields = [
            'id', 'startup_id', 'title', 'description', 'business_plan',
            'media_files', 'status', 'duration',
            'funding_goal', 'current_funding', 'category_id', 'website',
            'email', 'has_patents', 'is_participant', 'is_active',
            'created_at', 'updated_at', 'technologies_used', 'milestones'
        ]
        read_only_fields = ('startup_id',)

    def validate_funding_goal(self, value):
        """
        Ensure funding_goal is a positive decimal with at most 20 digits.
        """
        if len(str(value).replace('.', '').replace('-', '')) > 20:
            raise serializers.ValidationError('Funding goal is too large.')
        if value <= 0:
            raise serializers.ValidationError('Funding goal must be greater than 0.')
        return value

    def validate(self, data):
        """
        Cross-field validation for Project.
        - current_funding must not exceed funding_goal
        - business_plan required for in_progress or completed
        - funding_goal required if is_participant is True
        """
        getattr(self, 'instance', None)
        funding_goal = get_field_value(self, data, 'funding_goal')
        current_funding = get_field_value(self, data, 'current_funding') or Decimal('0.00')
        business_plan = get_field_value(self, data, 'business_plan')
        status = get_field_value(self, data, 'status')
        is_participant = get_field_value(self, data, 'is_participant') or False
        errors = {}

        if funding_goal is not None and Decimal(str(current_funding)) > Decimal(str(funding_goal)):
            errors['current_funding'] = 'Current funding cannot exceed funding goal.'

        if funding_goal is not None and current_funding >= funding_goal and not business_plan:
            errors['business_plan'] = 'Business plan is required when funding goal is reached.'

        if status in [ProjectStatus.IN_PROGRESS, ProjectStatus.COMPLETED] and not business_plan:
            errors['business_plan'] = 'Business plan is required for projects in progress or completed.'

        if is_participant and funding_goal is None:
            errors['funding_goal'] = 'Funding goal is required for participant projects.'

        if errors:
            raise serializers.ValidationError(errors)

        return data

class ProjectDocumentSerializer(DocumentSerializer):
    """
    Serializer for the Elasticsearch ProjectDocument.
    """

    class Meta:
        document = ProjectDocument
        fields = ('id', 'title', 'description', 'status', 'startup', 'category')

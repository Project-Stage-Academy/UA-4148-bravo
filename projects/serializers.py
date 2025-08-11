from decimal import Decimal
from rest_framework import serializers
from projects.models import Project, Category
from startups.models import Startup
from common.enums import ProjectStatus
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from projects.documents import ProjectDocument
from startups.serializers.startup_project import StartupProjectSerializer
from utils.get_field_value import get_field_value


class CategorySerializer(serializers.ModelSerializer):
    """Read-only serializer for category details."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class ProjectReadSerializer(serializers.ModelSerializer):
    """Serializer for reading Project with nested related objects."""

    category = CategorySerializer(read_only=True)
    startup = StartupProjectSerializer(read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'startup', 'title', 'description', 'business_plan',
            'media_files', 'status', 'status_display', 'duration',
            'funding_goal', 'current_funding', 'category', 'website', 'email',
            'has_patents', 'is_participant', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_status_display(self, obj):
        return ProjectStatus(obj.status).label if obj.status else None


class ProjectWriteSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Project with validation."""

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category'
    )
    startup_id = serializers.PrimaryKeyRelatedField(
        queryset=Startup.objects.all(),
        source='startup'
    )
    funding_goal = serializers.DecimalField(
        max_digits=20,
        decimal_places=2
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
            'startup_id', 'title', 'description', 'business_plan',
            'media_files', 'status', 'duration',
            'funding_goal', 'current_funding', 'category_id', 'website',
            'email', 'has_patents', 'is_participant', 'is_active'
        ]

    def validate(self, data):
        """
        Cross-field validation logic based on business rules:
        - current_funding must not exceed funding_goal
        - business_plan required for in_progress or completed
        - funding_goal required if is_participant is True
        """
        funding_goal = get_field_value(self, data, 'funding_goal')
        current_funding = get_field_value(self, data, 'current_funding') or Decimal('0.00')
        status = get_field_value(self, data, 'status')
        business_plan = get_field_value(self, data, 'business_plan')
        is_participant = get_field_value(self, data, 'is_participant')

        errors = {}

        if funding_goal is not None and current_funding > funding_goal:
            errors['current_funding'] = 'Current funding cannot exceed funding goal.'

        if funding_goal is not None and current_funding >= funding_goal and not business_plan:
            errors['business_plan'] = 'Business plan is required when funding goal is reached.'

        if status in [ProjectStatus.IN_PROGRESS, ProjectStatus.COMPLETED] and not business_plan:
            errors['business_plan'] = 'Business plan is required for projects in progress or completed.'

        if is_participant and not funding_goal:
            errors['funding_goal'] = 'Funding goal is required for participant projects.'

        if errors:
            raise serializers.ValidationError(errors)

        return data


class ProjectDocumentSerializer(DocumentSerializer):
    class Meta:
        document = ProjectDocument
        fields = ('id', 'title', 'description', 'status', 'startup', 'category')

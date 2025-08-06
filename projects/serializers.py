from decimal import Decimal
from rest_framework import serializers

from projects.models import Project, Category
from profiles.models import Startup
from common.enums import ProjectStatus


class CategorySerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying category details."""
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class StartupSerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying startup details."""
    class Meta:
        model = Startup
        fields = ['id', 'company_name', 'stage', 'website']


class ProjectSerializer(serializers.ModelSerializer):
    """Main serializer for Project with validation logic and nested read-only fields."""
    category = CategorySerializer(read_only=True)
    startup = StartupSerializer(read_only=True)

    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    startup_id = serializers.PrimaryKeyRelatedField(
        queryset=Startup.objects.all(),
        source='startup',
        write_only=True
    )

    funding_goal = serializers.DecimalField(
        required=True,
        max_digits=20,
        decimal_places=2
    )
    current_funding = serializers.DecimalField(
        required=False,
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )

    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'startup', 'startup_id',
            'title', 'description',
            'business_plan', 'media_files',
            'status', 'status_display', 'duration',
            'funding_goal', 'current_funding',
            'category', 'category_id',
            'website', 'email',
            'has_patents', 'is_participant', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_status_display(self, obj):
        return ProjectStatus(obj.status).label if obj.status else None

    def validate(self, data):
        """
        Cross-field validation logic based on business rules:
        - current_funding must not exceed funding_goal
        - business_plan required for in_progress or completed
        - funding_goal required if is_participant is True
        """
        funding_goal = data.get('funding_goal')
        current_funding = data.get('current_funding', Decimal('0.00'))
        status = data.get('status')
        business_plan = data.get('business_plan')
        is_participant = data.get('is_participant')

        # fallback to instance values for partial updates
        if self.instance:
            funding_goal = funding_goal if funding_goal is not None else self.instance.funding_goal
            current_funding = current_funding if current_funding is not None else self.instance.current_funding
            status = status if status is not None else self.instance.status
            business_plan = business_plan if business_plan is not None else self.instance.business_plan
            is_participant = is_participant if is_participant is not None else self.instance.is_participant

        errors = {}

        if funding_goal is not None and current_funding > funding_goal:
            errors['current_funding'] = 'Current funding cannot exceed funding goal.'

        if status in [ProjectStatus.IN_PROGRESS, ProjectStatus.COMPLETED] and not business_plan:
            errors['business_plan'] = 'Business plan is required for projects in progress or completed.'

        if is_participant and not funding_goal:
            errors['funding_goal'] = 'Funding goal is required for participant projects.'

        if errors:
            raise serializers.ValidationError(errors)

        return data


from rest_framework import serializers
from projects.models import Project, Category
from profiles.models import Startup


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

    class Meta:
        model = Project
        fields = [
            'id', 'startup', 'startup_id',
            'title', 'description',
            'business_plan', 'media_files',
            'status', 'duration',
            'funding_goal', 'current_funding',
            'category', 'category_id',
            'website', 'email',
            'has_patents', 'is_participant', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Cross-field validation logic based on business rules:
        - current_funding must not exceed funding_goal
        - business_plan required for in_progress or completed
        - funding_goal required if is_participant is True
        """
        errors = {}

        funding_goal = data.get('funding_goal') or getattr(self.instance, 'funding_goal', None)
        current_funding = data.get('current_funding') or getattr(self.instance, 'current_funding', None)
        status = data.get('status') or getattr(self.instance, 'status', None)
        business_plan = data.get('business_plan') or getattr(self.instance, 'business_plan', None)
        is_participant = data.get('is_participant') or getattr(self.instance, 'is_participant', None)

        if funding_goal is not None and current_funding and current_funding > funding_goal:
            errors['current_funding'] = 'Current funding cannot exceed funding goal.'

        if status in ['in_progress', 'completed'] and not business_plan:
            errors['business_plan'] = 'Business plan is required for projects in progress or completed.'

        if is_participant and not funding_goal:
            errors['funding_goal'] = 'Funding goal is required for participant projects.'

        if errors:
            raise serializers.ValidationError(errors)

        return data


from decimal import Decimal
from rest_framework import serializers

from projects.models import Project, Category
from profiles.models import Startup
from common.enums import ProjectStatus

from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from projects.documents import ProjectDocument

from rest_framework import serializers
from .models import Subscription, Project

class ProjectSerializer(serializers.ModelSerializer):
    startup_name = serializers.CharField(source='startup.company_name', read_only=True)
    startup_logo = serializers.ImageField(source='startup.logo', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'startup_name', 'startup_logo',
            'funding_goal', 'current_funding', 'status', 'created_at'
        ]

class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['project', 'investment_amount']
        read_only_fields = ['investor']

    def validate(self, data):
        project = data.get('project')
        investment_amount = data.get('investment_amount')

        if not project:
            raise serializers.ValidationError({"project": "This field is required."})

        if project.current_funding >= project.funding_goal:
            raise serializers.ValidationError("This project is already fully funded.")

        remaining_funding = project.funding_goal - project.current_funding
        if investment_amount > remaining_funding:
            raise serializers.ValidationError(
                f"The investment amount exceeds the remaining funding. Only {remaining_funding} is available."
            )
            
        return data

    def create(self, validated_data):
        project = validated_data['project']
        investment_amount = validated_data['investment_amount']
        
        project.current_funding += investment_amount
        project.save()

        return Subscription.objects.create(
            investor=self.context['request'].user,
            **validated_data
        )


class CategorySerializer(serializers.ModelSerializer):
    """
    Read-only serializer for displaying category details.
    """
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class StartupSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for displaying startup details.
    """
    class Meta:
        model = Startup
        fields = ['id', 'company_name', 'stage', 'website']


class ProjectSerializer(serializers.ModelSerializer):
    """
    Main serializer for Project.
    Includes nested read-only fields and cross-field validation logic.
    """
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
        """
        Returns the human-readable label for the project's status.
        """
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


class ProjectDocumentSerializer(DocumentSerializer):
    class Meta:
        document = ProjectDocument
        fields = ('id', 'title', 'description', 'status', 'startup', 'category')
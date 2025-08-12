from decimal import Decimal
from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from projects.models import Project, Category
from startups.models import Startup
from common.enums import ProjectStatus

from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from projects.documents import ProjectDocument

from investments.models import Subscription

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
    Main serializer for the Project model, including nested fields,
    custom method fields for startup details, and validation logic.
    """
    category = CategorySerializer(read_only=True)
    startup = StartupSerializer(read_only=True)
    startup_name = serializers.SerializerMethodField()
    startup_logo = serializers.SerializerMethodField()

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
            'id', 'startup', 'startup_id', 'startup_name', 'startup_logo',
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

    def get_startup_name(self, obj):
        """
        Returns the name of the associated startup, or None if no startup is linked.
        """
        return obj.startup.company_name if obj.startup else None

    def get_startup_logo(self, obj):
        """
        Returns the URL of the startup's logo, or None if no logo or startup exists.
        """
        request = self.context.get('request')
        if obj.startup and obj.startup.logo:
            return request.build_absolute_uri(obj.startup.logo.url)
        return None

    def get_startup_name(self, obj):
        """
        Returns the name of the associated startup, or None if no startup is linked.
        """
        return obj.startup.company_name if obj.startup else None

    def get_startup_logo(self, obj):
        """
        Returns the URL of the startup's logo, or None if no logo or startup exists.
        """
        request = self.context.get('request')
        if obj.startup and obj.startup.logo:
            return request.build_absolute_uri(obj.startup.logo.url)
        return None

    def validate(self, data):
        """
        Cross-field validation logic based on business rules:
        - current_funding must not exceed funding_goal
        - business_plan required for in_progress or completed
        - funding_goal required if is_participant is True
        - investment amounts must be positive (handled in SubscriptionCreateSerializer)
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

        if funding_goal is not None and Decimal(str(current_funding)) > Decimal(str(funding_goal)):
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


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new investment subscription.
    Handles validation for investment amount and project status.
    Uses atomic updates to prevent race conditions.
    """
    class Meta:
        model = Subscription
        fields = ['project', 'investment_amount']
        read_only_fields = ['investor']

    def validate(self, data):
        """
        Validates the investment amount and the state of the project.
        """
        project = data.get('project')
        investment_amount = data.get('investment_amount')
        user = self.context['request'].user

        # 1. Validate required fields
        if not project:
            raise serializers.ValidationError({"project": "This field is required."})

        # 2. Check for authenticated user and investment permissions
        if not user or not user.is_authenticated:
            raise serializers.ValidationError({"user": "Authentication is required to make an investment."})
        
        # Here, we assume the startup owner cannot invest in their own project.
        if project.startup and user == project.startup.owner:
            raise serializers.ValidationError({"user": "You cannot invest in your own project."})

        # 3. Validate investment amount
        if investment_amount is None or investment_amount <= 0:
            raise serializers.ValidationError({"investment_amount": "Investment amount must be a positive number."})

        current_funding = Decimal(str(project.current_funding))
        funding_goal = Decimal(str(project.funding_goal))

        # 4. Check project funding status
        if current_funding >= funding_goal:
            raise serializers.ValidationError("This project is already fully funded.")

        remaining_funding = funding_goal - current_funding
        if investment_amount > remaining_funding:
            raise serializers.ValidationError(
                f"The investment amount exceeds the remaining funding. Only {remaining_funding} is available."
            )
        
        return data

    def create(self, validated_data):
        """
        Creates a new subscription and atomically updates the project's funding.
        """
        project = validated_data['project']
        investment_amount = validated_data['investment_amount']
        investor = self.context['request'].user

        with transaction.atomic():
            project.refresh_from_db()

            project.current_funding = F('current_funding') + investment_amount
            project.save()

            project.refresh_from_db()

            subscription = Subscription.objects.create(
                investor=investor,
                **validated_data
            )
        
        return subscription


class ProjectDocumentSerializer(DocumentSerializer):
    """
    Serializer for the Elasticsearch ProjectDocument.
    """
    class Meta:
        document = ProjectDocument
        fields = ('id', 'title', 'description', 'status', 'startup', 'category')

from rest_framework import serializers

from profiles.models import Startup, Investor
from projects.serializers import ProjectSerializer
from common.enums import Stage
from validation.validate_social_links import SocialLinksValidationMixin


class StartupShortSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for nested use (e.g., inside Investor).
    """
    class Meta:
        model = Startup
        fields = [
            'id', 'company_name', 'industry', 'country',
            'website', 'stage', 'is_participant'
        ]
        read_only_fields = fields


class StartupSerializer(SocialLinksValidationMixin, serializers.ModelSerializer):
    """
    Full serializer for Startup.
    Uses shared mixin for social_links validation.
    Includes nested project details.
    """
    projects = ProjectSerializer(many=True, read_only=True)
    social_links = serializers.DictField(required=False)

    class Meta:
        model = Startup
        fields = [
            'id', 'company_name', 'description', 'industry',
            'country', 'website', 'email', 'phone',
            'contact_person', 'location', 'status',
            'stage', 'social_links', 'is_participant',
            'founded_at', 'team_size', 'is_active',
            'user', 'created_at', 'updated_at',
            'projects'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'projects']

    def validate_company_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Company name must not be empty.")
        return value

    def validate_social_links(self, value):
        """
        Delegates validation to the shared mixin.
        """
        return super().validate_social_links(value)

    def validate(self, data):
        """
        Cross-field validation logic:
        - team_size must be at least 1
        - either website or email must be provided
        - industry, country, and user must be present
        """
        errors = {}

        team_size = data.get('team_size')
        website = data.get('website')
        email = data.get('email')

        if team_size is not None and team_size < 1:
            errors['team_size'] = "Team size must be at least 1."

        if not website and not email:
            errors['contact'] = "At least one contact method (website or email) must be provided."

        required_fields = ['industry', 'country', 'user']
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            errors['missing_fields'] = f"Missing required fields: {', '.join(missing)}"

        if errors:
            raise serializers.ValidationError(errors)

        return data


class InvestorSerializer(SocialLinksValidationMixin, serializers.ModelSerializer):
    """
    Full serializer for Investor.
    Uses shared mixin for social_links validation.
    Includes nested startup details.
    """
    social_links = serializers.DictField(required=False)

    startups = serializers.PrimaryKeyRelatedField(
        queryset=Startup.objects.all(),
        many=True,
        required=False,
        help_text="List of startup IDs this investor is associated with"
    )
    startup_details = StartupShortSerializer(
        source='startups',
        many=True,
        read_only=True
    )

    class Meta:
        model = Investor
        fields = [
            'id', 'company_name', 'email', 'phone', 'country',
            'fund_size', 'stage', 'is_active', 'social_links',
            'startups', 'startup_details', 'user',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'startup_details']

    def validate_company_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Company name must not be empty.")
        return value

    def validate_social_links(self, value):
        """
        Delegates validation to the shared mixin.
        """
        return super().validate_social_links(value)


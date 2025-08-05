from urllib.parse import urlparse
from rest_framework import serializers
from profiles.models import Startup, Investor
from projects.serializers import ProjectSerializer
from common.company import Stage


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


class StartupSerializer(serializers.ModelSerializer):
    """
    Full serializer for Startup.
    Includes validation for company_name, social_links, and cross-field logic.
    """
    projects = ProjectSerializer(many=True, read_only=True)

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
        if not value.strip():
            raise serializers.ValidationError("Company name must not be empty.")
        return value

    def validate_social_links(self, value):
        allowed_domains = Startup.ALLOWED_SOCIAL_PLATFORMS

        errors = {}
        for platform, url in value.items():
            platform_lc = platform.lower()
            if platform_lc not in allowed_domains:
                errors[platform] = f"Platform '{platform}' is not supported."
                continue

            domain = urlparse(url).netloc.lower()
            if not any(allowed in domain for allowed in allowed_domains[platform_lc]):
                errors[platform] = f"Invalid URL for platform '{platform}': {url}"

        if errors:
            raise serializers.ValidationError({'social_links': errors})

        return value

    def validate(self, data):
        errors = {}

        team_size = data.get('team_size')
        website = data.get('website')
        email = data.get('email')

        if team_size is not None and team_size < 1:
            errors['team_size'] = "Team size must be at least 1."

        if not website and not email:
            errors['contact'] = "At least one contact method (website or email) must be provided."

        if errors:
            raise serializers.ValidationError(errors)

        return data


class InvestorSerializer(serializers.ModelSerializer):
    """
    Full serializer for Investor.
    Includes validation and nested startup details.
    """
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
        if not value.strip():
            raise serializers.ValidationError("Company name must not be empty.")
        return value

    def validate_social_links(self, value):
        allowed_domains = Startup.ALLOWED_SOCIAL_PLATFORMS

        errors = {}
        for platform, url in value.items():
            platform_lc = platform.lower()
            if platform_lc not in allowed_domains:
                errors[platform] = f"Platform '{platform}' is not supported."
                continue

            domain = urlparse(url).netloc.lower()
            if not any(allowed in domain for allowed in allowed_domains[platform_lc]):
                errors[platform] = f"Invalid URL for platform '{platform}': {url}"

        if errors:
            raise serializers.ValidationError({'social_links': errors})

        return value



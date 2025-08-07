from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers
from rest_framework import serializers
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from startups.documents import StartupDocument
from core import settings
from projects.serializers import ProjectSerializer
from startups.documents import StartupDocument
from startups.models import Startup
from validation.validate_social_links import validate_social_links_dict


class SocialLinksValidationMixin:
    """
    Provides validation logic for the `social_links` field.

    This method ensures that:
    - Each platform key is supported (based on settings.ALLOWED_SOCIAL_PLATFORMS).
    - Each URL is syntactically valid.
    - The domain of each URL matches one of the expected domains for the given platform.

    Args:
        value (dict): A dictionary of platform names mapped to URLs.

    Returns:
        dict: The validated `social_links` dictionary.

    Raises:
        serializers.ValidationError: If any platform is unsupported, any URL is malformed,
                                     or any domain does not match the expected values.
    """

    def validate_social_links(self, value):
        validate_social_links_dict(
            social_links=value,
            allowed_platforms=settings.ALLOWED_SOCIAL_PLATFORMS,
            raise_serializer=True
        )
        return value


class StartupDocumentSerializer(DocumentSerializer):
    industries = serializers.SerializerMethodField()

    class Meta:
        document = StartupDocument
        fields = ('id', 'company_name', 'description', 'location', 'funding_stage', 'industries')

    def get_industries(self, obj):
        if obj.industries:
            return [industry.name for industry in obj.industries]
        return []


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

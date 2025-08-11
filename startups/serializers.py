from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers
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


class StartupSerializer(SocialLinksValidationMixin, serializers.ModelSerializer):
    """
    Full serializer for Startup.
    Includes nested project details.
    """
    projects = ProjectSerializer(many=True, read_only=True)
    social_links = serializers.DictField(required=False)

    class Meta:
        model = Startup
        fields = [
            'id', 'company_name', 'description', 'industry',
            'location', 'website', 'email', 'founded_year',
            'team_size', 'stage', 'social_links', 'user',
            'created_at', 'updated_at', 'projects'
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
        - industry, location, and user must be present
        """
        errors = {}

        team_size = data.get('team_size')
        website = data.get('website', '').strip()
        email = data.get('email', '').strip()

        if team_size is not None and team_size < 1:
            errors['team_size'] = "Team size must be at least 1."

        if not website and not email:
            errors['non_field_errors'] = [
                "At least one contact method (website or email) must be provided."
            ]

        required_fields = ['industry', 'location', 'user']
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            errors['missing_fields'] = f"Missing required fields: {', '.join(missing)}"

        if errors:
            raise serializers.ValidationError(errors)

        return data


class StartupDocumentSerializer(DocumentSerializer):
    industry = serializers.SerializerMethodField()

    class Meta:
        document = StartupDocument
        fields = ('id', 'company_name', 'description', 'location', 'stage', 'industry')

    def get_industry(self, obj):
        return obj.industry.name if obj.industry else None


class StartupShortSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for nested use (e.g., inside Investor).
    """

    class Meta:
        model = Startup
        fields = [
            'id', 'company_name', 'industry', 'location',
            'website', 'stage'
        ]
        read_only_fields = fields

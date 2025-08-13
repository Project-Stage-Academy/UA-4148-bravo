from rest_framework import serializers
from .models import Startup
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from .documents import StartupDocument


class StartupSerializer(serializers.ModelSerializer):
    # Social links field with optional URLs
    social_links = serializers.DictField(
        child=serializers.URLField(required=False, allow_blank=True),
        required=False
    )

    class Meta:
        model = Startup
        fields = '__all__'

    def validate_company_name(self, value):
        # Ensure company name is not empty or only spaces
        if not value or not value.strip():
            raise serializers.ValidationError("Company name cannot be empty.")
        return value

    def validate(self, attrs):
        # Either email or website must be provided
        email = attrs.get('email')
        website = attrs.get('website')
        if not email and not website:
            raise serializers.ValidationError({
                'email': ["Either email or website must be provided."],
                'website': ["Either email or website must be provided."]
            })

        # Team size must be greater than zero if provided
        team_size = attrs.get('team_size')
        if team_size is not None and team_size <= 0:
            raise serializers.ValidationError({
                'team_size': ["Team size must be greater than zero."]
            })

        # Social links validation
        social_links = attrs.get('social_links', {})
        allowed_domains = {
            'linkedin': 'linkedin.com',
            'twitter': 'twitter.com',
            'facebook': 'facebook.com',
            'instagram': 'instagram.com'
        }

        if isinstance(social_links, dict):
            errors = {}
            for platform, url in social_links.items():
                if platform not in allowed_domains:
                    errors[platform] = [f"Platform '{platform}' is not supported."]
                else:
                    expected_domain = allowed_domains[platform]
                    if url and expected_domain not in url:
                        errors[platform] = [f"Invalid domain for {platform}. Must contain '{expected_domain}'."]
            if errors:
                raise serializers.ValidationError({'social_links': errors})

        return attrs


class StartupDocumentSerializer(DocumentSerializer):
    class Meta:
        document = StartupDocument
        fields = (
            'id',
            'company_name',
            'description',
            'website',
            'email',
            'founded_year',
            'team_size',
            'funding_stage',
            'investment_needs',
            'company_size',
            'is_active',
            'created_at',
            'updated_at',
            'industry',
            'location',
        )

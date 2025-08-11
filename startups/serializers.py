from rest_framework import serializers
from .models import Startup, Industry, Location
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from .documents import StartupDocument


class StartupSerializer(serializers.ModelSerializer):
    social_links = serializers.DictField(
        child=serializers.URLField(required=False, allow_blank=True),
        required=False
    )

    class Meta:
        model = Startup
        fields = '__all__'

    def validate_company_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Company name cannot be empty.")
        return value.strip()

    def validate(self, attrs):
        if not attrs.get('email') and not attrs.get('website'):
            raise serializers.ValidationError({
                'email': ["Either email or website must be provided."]
            })

        team_size = attrs.get('team_size')
        if team_size is not None and team_size <= 0:
            raise serializers.ValidationError({
                'team_size': ["Team size must be greater than zero."]
            })

        social_links = attrs.get('social_links', {})
        allowed_domains = {
            'linkedin': 'linkedin.com',
            'twitter': 'twitter.com',
            'facebook': 'facebook.com',
            'instagram': 'instagram.com'
        }

        if isinstance(social_links, dict):
            for platform, url in social_links.items():
                if platform not in allowed_domains:
                    raise serializers.ValidationError({
                        'social_links': {
                            platform: [f"Platform '{platform}' is not supported."]
                        }
                    })
                expected_domain = allowed_domains[platform]
                if expected_domain not in url:
                    raise serializers.ValidationError({
                        'social_links': {
                            platform: [f"Invalid domain for {platform}. Must contain '{expected_domain}'."]
                        }
                    })

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

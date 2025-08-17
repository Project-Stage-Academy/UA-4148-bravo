from rest_framework import serializers
from mixins.social_links_mixin import SocialLinksValidationMixin
from startups.models import Startup
from utils.get_field_value import get_field_value


class StartupBaseSerializer(SocialLinksValidationMixin, serializers.ModelSerializer):
    """
    Base serializer for Startup model.
    Contains shared fields and cross-field validation.
    """
    social_links = serializers.DictField(required=False)

    class Meta:
        model = Startup
        fields = [
            'id', 'company_name', 'description', 'industry',
            'location', 'website', 'email', 'founded_year',
            'team_size', 'stage', 'social_links', 'user',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_company_name(self, value):
        """
        Ensure company name is not empty or only spaces.
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Company name must not be empty.")
        return value

    def validate(self, data):
        """
        Cross-field validation:
        - team_size must be at least 1
        - either website or email must be provided
        - industry, location, and user must be present
        - social_links validation is handled by SocialLinksValidationMixin
        """
        errors = {}

        # Team size validation
        team_size = get_field_value(self, data, 'team_size')
        if team_size is not None and team_size < 1:
            errors['team_size'] = "Team size must be at least 1."

        # Contact method validation
        website = get_field_value(self, data, 'website')
        website = website.strip() if website else ""

        email = get_field_value(self, data, 'email')
        email = email.strip() if email else ""

        if not website and not email:
            errors['website'] = "At least one contact method (website or email) must be provided."
            errors['email'] = "At least one contact method (website or email) must be provided."

        # Required foreign keys
        for field in ['industry', 'location', 'user']:
            if not get_field_value(self, data, field):
                errors[field] = f"{field.replace('_', ' ').capitalize()} is required."

        if errors:
            raise serializers.ValidationError(errors)

        return data


from rest_framework import serializers

from investors.models import Investor
from startups.models import Startup
from startups.serializers import StartupShortSerializer, SocialLinksValidationMixin


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

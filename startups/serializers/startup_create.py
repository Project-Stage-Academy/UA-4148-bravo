from rest_framework import serializers
from startups.models import Startup, Industry, Location
from common.company import Company
from mixins.social_links_mixin import SocialLinksValidationMixin

class StartupCreateSerializer(SocialLinksValidationMixin, serializers.ModelSerializer):
    """
    Serializer for creating a new Startup profile.

    This serializer handles the validation and creation of a Startup instance.
    The 'user' field is automatically populated from the authenticated user
    making the request, and is not required in the input payload.
    It validates that the company name is unique.
    """
    industry = serializers.PrimaryKeyRelatedField(
        queryset=Industry.objects.all(),
        allow_null=True,
        required=False
    )
    location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Startup
        fields = [
            'id', 'company_name', 'description', 'industry', 'location', 'website',
            'email', 'founded_year', 'team_size', 'stage', 'social_links'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'company_name': {'required': True},
            'email': {'required': True},
            'founded_year': {'required': True},
        }

    def validate_company_name(self, value):
        """
        Ensure the company name is unique, case-insensitively.
        """
        if self.instance is None and Startup.objects.filter(company_name__iexact=value).exists():
            raise serializers.ValidationError("A startup with this name already exists.")
        return value

    def create(self, validated_data):
        """
        Create a new Startup instance, associating it with the request user.
        """
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("Authenticated user not found in context.")

        user = request.user

        if Startup.objects.filter(user=user).exists() or hasattr(user, 'investor'):
            raise serializers.ValidationError({"detail": "You have already created a company profile."})

        validated_data['user'] = user
        return Startup.objects.create(**validated_data)
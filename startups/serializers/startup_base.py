from rest_framework import serializers
from mixins.social_links_mixin import SocialLinksValidationMixin
from startups.models import Startup
from utils.get_field_value import get_field_value
from validation.validate_names import validate_company_name, validate_latin
from django.core.exceptions import ValidationError


class StartupBaseSerializer(SocialLinksValidationMixin, serializers.ModelSerializer):
    """
    Base serializer for Startup model.
    Contains shared fields and validations.
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
        extra_kwargs = {
            'company_name': {
                'validators': []
            },
            'email': {
                'validators': []
            }
        }

    def validate_company_name(self, value):
        """ Validate company name using shared validation function. """
        try:
            value = validate_company_name(value)
            if not validate_latin(value):
                raise ValidationError(
                    "The name must contain only Latin letters, spaces, hyphens, or apostrophes."
                )

            if self.instance:
                if Startup.objects.filter(company_name__iexact=value).exclude(pk=self.instance.pk).exists():
                    raise ValidationError("Company with this name already exists.")
            else:
                if Startup.objects.filter(company_name__iexact=value).exists():
                    raise ValidationError("Company with this name already exists.")

            return value
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def validate_email(self, value):
        """ Validate email uniqueness. """
        if value:
            value = value.strip().lower()

            if self.instance:
                if Startup.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
                    raise ValidationError("Company with this email already exists.")
            else:
                if Startup.objects.filter(email__iexact=value).exists():
                    raise ValidationError("Company with this email already exists.")

        return value

    def validate(self, data):
        """
        Cross-field validation:
        - team_size must be at least 1
        - either website or email must be provided
        - industry, location, and user must be present
        """
        errors = {}

        team_size = get_field_value(self, data, 'team_size')
        if team_size is not None and team_size < 1:
            errors['team_size'] = "Team size must be at least 1."

        website = get_field_value(self, data, 'website')
        website = website.strip() if website else ""

        email = get_field_value(self, data, 'email')
        email = email.strip() if email else ""

        if not website and not email:
            errors['website'] = "At least one contact method (website or email) must be provided."
            errors['email'] = "At least one contact method (website or email) must be provided."

        for field in ['industry', 'location', 'user']:
            if not get_field_value(self, data, field):
                errors[field] = f"{field.replace('_', ' ').capitalize()} is required."

        if errors:
            raise serializers.ValidationError(errors)

        return data

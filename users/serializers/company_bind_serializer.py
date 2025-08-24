from rest_framework import serializers
from django.core.exceptions import ValidationError
from investors.models import Investor
from startups.models import Startup
from validation.validate_names import validate_forbidden_names
from validation.validate_string_fields import validate_max_length


class CompanyBindingSerializer(serializers.Serializer):
    """ Serializer for validating company binding requests. """
    company_name = serializers.CharField(max_length=254, allow_blank=True)
    company_type = serializers.ChoiceField(choices=['startup', 'investor'])

    class Meta:
        extra_kwargs = {
            'company_name': {
                'validators': []
            }
        }

    def validate_company_name(self, value):
        """
        Validate company name using existing validation functions.
        Aggregate all validation errors instead of returning only the first one.
        Check if company name already exists for both Startup and Investor.
        """
        error_messages = []

        try:
            validate_forbidden_names(value, "company_name")
        except ValidationError as e:
            if hasattr(e, 'error_list'):
                error_messages.extend([str(err) for err in e.error_list])
            else:
                error_messages.append(str(e))

        try:
            validate_max_length(value, 254, "Company name")
        except ValidationError as e:
            if hasattr(e, 'error_list'):
                error_messages.extend([str(err) for err in e.error_list])
            else:
                error_messages.append(str(e))

        if Startup.objects.filter(company_name__iexact=value).exists():
            error_messages.append("Startup with this name already exists.")

        if Investor.objects.filter(company_name__iexact=value).exists():
            error_messages.append("Investor with this name already exists.")

        if error_messages:
            raise serializers.ValidationError(error_messages)

        return value

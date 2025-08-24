from rest_framework import serializers
from django.core.exceptions import ValidationError
from validation.validate_names import validate_forbidden_names
from validation.validate_string_fields import validate_max_length


class CompanyBindingSerializer(serializers.Serializer):
    """ Serializer for validating company binding requests. """
    company_name = serializers.CharField(max_length=254, unique=True)
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
        """
        try:
            validate_forbidden_names(value, "company_name")
            validate_max_length(value, 254, "Company name")
        except ValidationError as e:
            error_messages = []
            if hasattr(e, 'error_dict'):
                for field_errors in e.error_dict.values():
                    error_messages.extend([str(err) for err in field_errors])
            else:
                error_messages = [str(e)]

            raise serializers.ValidationError(error_messages)

        return value

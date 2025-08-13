import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework import serializers
from common.enums import Stage
from investors.models import Investor


class InvestorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Investor model.
    Includes all fields defined in the abstract Company base class and Investor-specific fields.
    """
    company_name = serializers.CharField(
        max_length=254,
        allow_blank=False,
        error_messages={
            'blank': "Company name must not be empty.",
            'max_length': "Company name cannot exceed 254 characters."
        }
    )

    email = serializers.EmailField(
        max_length=254,
        required=True,
        error_messages={
            'blank': "Email is required.",
            'invalid': "Enter a valid email address.",
        }
    )

    founded_year = serializers.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(datetime.datetime.now().year)],
        error_messages={
            'min_value': "Founded year cannot be before 1900.",
            'max_value': "Founded year cannot be in the future."
        }
    )

    team_size = serializers.IntegerField(
        validators=[MinValueValidator(1)],
        error_messages={
            'min_value': "Team size must be at least 1."
        }
    )

    fund_size = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        error_messages={
            'min_value': "Fund size cannot be negative.",
            'max_digits': "Fund size is too large."
        }
    )

    stage = serializers.ChoiceField(
        choices=Stage.choices,
        default=Stage.MVP,
        error_messages={'invalid_choice': "Invalid stage choice."}
    )

    description = serializers.CharField(
        required=False,
        allow_blank=True
    )

    class Meta:
        model = Investor
        fields = [
            'id', 'user', 'industry', 'company_name', 'location',
            'logo', 'description', 'website', 'email', 'founded_year',
            'team_size', 'stage', 'fund_size', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']

    def validate_company_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Company name must not be empty.")
        return value

    def validate_description(self, value):
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Description must be at least 10 characters long if provided."
            )
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("Request user is missing in serializer context.")
        validated_data['user'] = request.user
        return super().create(validated_data)

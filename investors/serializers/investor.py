import datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import transaction
from rest_framework import serializers
from django.core.exceptions import ValidationError
from common.enums import Stage
from investors.models import Investor, SavedStartup, ViewedStartup
from startups.models import Startup
from validation.validate_names import validate_company_name


class InvestorSerializer(serializers.ModelSerializer):
    """
    Serializer for the Investor model.
    Includes all fields defined in the abstract Company base class and Investor-specific fields.
    """
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
        extra_kwargs = {
            'company_name': {
                'error_messages': {
                    'blank': "Company name must not be empty.",
                    'max_length': "Company name cannot exceed 254 characters."
                }
            },
            'email': {
                'error_messages': {
                    'blank': "Email is required.",
                    'invalid': "Enter a valid email address.",
                }
            }
        }

    def validate_company_name(self, value):
        """ Validate company name using shared validation function. """
        try:
            return validate_company_name(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

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


class SavedStartupSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and retrieving SavedStartup records.

    Ensures:
    - Only authenticated investors can save startups.
    - Prevents saving own startup.
    - Avoids duplicates via validator and IntegrityError handling.
    """
    investor = serializers.PrimaryKeyRelatedField(read_only=True)
    startup = serializers.PrimaryKeyRelatedField(queryset=Startup.objects.all(), write_only=True)
    startup_name = serializers.CharField(source='startup.company_name', read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = SavedStartup
        fields = [
            'id',
            'investor',
            'startup',
            'startup_name',
            'status', 'notes',
            'saved_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'investor', 'startup_name', 'saved_at', 'created_at', 'updated_at']
        extra_kwargs = {
            'investor': {'read_only': True, 'required': False},
            'startup': {'write_only': True},
        }

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        investor = getattr(user, 'investor', None)
        startup = attrs.get('startup')

        errors = {}
        if not investor:
            errors.setdefault('non_field_errors', []).append('Only investors can save startups.')

        if startup is not None and getattr(startup, 'user_id', None) == getattr(user, 'id', None):
            errors['startup'] = 'You cannot save your own startup.'

        if self.instance is None and startup is None:
            errors['startup'] = 'This field is required.'

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        investor = validated_data.pop('investor', getattr(user, 'investor', None))
        if not investor:
            raise serializers.ValidationError({'non_field_errors': ['Only authenticated investors can save startups.']})

        startup = validated_data.get('startup')
        status_val = validated_data.get('status', 'watching')
        notes_val = validated_data.get('notes')
        if notes_val is None:
            notes_val = ''

        with transaction.atomic():
            obj, created = SavedStartup.objects.get_or_create(
                investor=investor,
                startup=startup,
                defaults={'status': status_val, 'notes': notes_val},
            )

        if not created:
            raise serializers.ValidationError({'non_field_errors': ['Already saved.']})

        return obj

class ViewedStartupSerializer(serializers.ModelSerializer):
    startup_id = serializers.IntegerField(source="startup.id", read_only=True)
    company_name = serializers.CharField(source="startup.company_name", read_only=True)

    class Meta:
        model = ViewedStartup
        fields = ["id", "startup_id", "company_name", "viewed_at"]

class InvestorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = [
            'id', 'company_name', 'industry', 'stage', 'team_size',
        ]        

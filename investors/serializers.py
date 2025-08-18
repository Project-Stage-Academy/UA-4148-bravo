import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework import serializers
from common.enums import Stage
from investors.models import Investor, SavedStartup
from startups.models import Startup
from django.db import transaction


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
        error_messages={'blank': "Email is required.", 'invalid': "Enter a valid email address."}
    )

    founded_year = serializers.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(datetime.datetime.now().year)],
        error_messages={'min_value': "Founded year cannot be before 1900.", 'max_value': "Founded year cannot be in the future."}
    )

    team_size = serializers.IntegerField(
        validators=[MinValueValidator(1)],
        error_messages={'min_value': "Team size must be at least 1."}
    )

    fund_size = serializers.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        error_messages={'min_value': "Fund size cannot be negative."}
    )

    stage = serializers.ChoiceField(
        choices=Stage.choices,
        default=Stage.MVP,
        error_messages={'invalid_choice': "Invalid stage choice."}
    )

    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Investor
        fields = [
            'id', 'user', 'industry', 'company_name', 'location', 'logo',
            'description', 'website', 'email', 'founded_year', 'team_size',
            'stage', 'fund_size', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']

    def validate_company_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Company name must not be empty.")
        return value

    def validate_description(self, value):
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long if provided.")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            raise serializers.ValidationError("Request user is missing in serializer context.")
        validated_data['user'] = request.user
        return super().create(validated_data)


class SavedStartupSerializer(serializers.ModelSerializer):
    """
    Serializer for SavedStartup records.
    Ensures only authenticated investors can save startups,
    prevents saving own startup, and avoids duplicates.
    """
    investor = serializers.PrimaryKeyRelatedField(read_only=True)
    startup = serializers.PrimaryKeyRelatedField(queryset=Startup.objects.all(), write_only=True)
    startup_name = serializers.CharField(source='startup.company_name', read_only=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = SavedStartup
        fields = ['id', 'investor', 'startup', 'startup_name', 'status', 'notes', 'saved_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'investor', 'startup_name', 'saved_at', 'created_at', 'updated_at']

    def validate(self, attrs):
        user = getattr(self.context.get('request'), 'user', None)
        investor = getattr(user, 'investor', None)
        startup = attrs.get('startup')
        errors = {}

        if not investor:
            errors.setdefault('non_field_errors', []).append('Only investors can save startups.')

        if startup and getattr(startup, 'user_id', None) == getattr(user, 'id', None):
            errors['startup'] = 'You cannot save your own startup.'

        if self.instance is None and startup is None:
            errors['startup'] = 'This field is required.'

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        user = getattr(self.context.get('request'), 'user', None)
        investor = validated_data.pop('investor', getattr(user, 'investor', None))
        if not investor:
            raise serializers.ValidationError({'non_field_errors': ['Only authenticated investors can save startups.']})

        startup = validated_data.get('startup')
        status_val = validated_data.get('status', 'watching')
        notes_val = validated_data.get('notes') or ''

        with transaction.atomic():
            obj, created = SavedStartup.objects.get_or_create(
                investor=investor,
                startup=startup,
                defaults={'status': status_val, 'notes': notes_val},
            )

        if not created:
            raise serializers.ValidationError({'non_field_errors': ['Already saved.']})

        return obj

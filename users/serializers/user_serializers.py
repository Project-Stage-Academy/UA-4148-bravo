from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from djoser.serializers import UserSerializer
from rest_framework import serializers
from users.models import UserRole
from users.validators import CustomPasswordValidator
from django.contrib.auth.password_validation import validate_password
from users.constants import CompanyType

User = get_user_model()
custom_password_validator = CustomPasswordValidator()


class CustomUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = User
        fields = ('user_id', 'username', 'email')


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """
    Custom user registration serializer that handles user creation with role assignment.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        min_length=8,
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'password2')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }

    def validate_email(self, value):
        """Validate that the email is not already in use."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists.", code="conflict"
            )
        return value.lower()

    def validate_password(self, value):
        """Apply global Django password validators (length, similarity, common, numeric, custom)."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, data):
        """Validate the entire user data."""
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        try:
            validate_email(data.get('email'))
        except DjangoValidationError:
            raise serializers.ValidationError({"email": "Enter a valid email address."})

        return data

    def create(self, validated_data):
        """Create and return a new user with the USER role by default."""
        validated_data.pop('password2', None)

        user_role, created = UserRole.objects.get_or_create(role=UserRole.Role.USER)

        user = User.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
            role=user_role
        )

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'email', 'first_name', 'last_name', 'user_phone', 'title', 'role']


class CurrentUserSerializer(serializers.ModelSerializer):
    """Public serializer for the currently logged-in user."""
    role = serializers.SerializerMethodField()

    def get_role(self, obj):
        return obj.role.role if obj.role else None

    class Meta:
        model = User
        fields = ("user_id", "email", "first_name", "last_name", "user_phone", "title", "role")
        read_only_fields = ("user_id", "email", "first_name", "last_name", "user_phone", "title", "role")

class ExtendedCurrentUserSerializer(CurrentUserSerializer):
    company_type = serializers.SerializerMethodField()
    company_id = serializers.SerializerMethodField()

    class Meta(CurrentUserSerializer.Meta):
        model = CurrentUserSerializer.Meta.model
        fields = CurrentUserSerializer.Meta.fields + ("company_type", "company_id")

    def get_company(self, obj):
        for attr, ctype in (("startup", CompanyType.STARTUP), ("investor", CompanyType.INVESTOR)):
            val = getattr(obj, attr, None)
            if val is not None:
                return attr, val.id
        return None, None

    def get_company_type(self, obj):
        company_type, _ = self.get_company(obj)
        return company_type

    def get_company_id(self, obj):
        _, company_id = self.get_company(obj)
        return company_id

class ResendEmailSerializer(serializers.Serializer):
    """
    Serializer for resending a verification email.

    This serializer is used to validate the request payload for the endpoint
    that allows resending an email verification link to a user.
    It does not reveal whether the user exists, for security purposes.

    Attributes:
        user_id (IntegerField): The ID of the target user. Must be a positive integer.
        token (CharField): The current verification token. Can be empty if a new token should be generated.
        email (EmailField, optional): A new email address to send the verification link to.
            If provided, it will override the stored email.
    """
    user_id = serializers.IntegerField(min_value=1)
    token = serializers.CharField(allow_blank=True, required=False)
    email = serializers.EmailField(required=False)

    def validate_email(self, value):
        """
        Normalize and validate the provided email address.

        This method converts the email to lowercase. It does not raise errors
        about whether the email already exists, to prevent user enumeration.

        Args:
            value (str): The email address provided in the request.

        Returns:
            str: The normalized (lowercased) email address.
        """
        return value.lower()

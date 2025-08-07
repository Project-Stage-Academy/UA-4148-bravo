from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
rom djoser.serializers import PasswordResetConfirmSerializer as BasePasswordResetConfirmSerializer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers
from .validators import CustomPasswordValidator
from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()
custom_password_validator = CustomPasswordValidator()


class CustomUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email') 

# Custom serializer for obtaining JWT with additional fields
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for obtaining JWT tokens.
    Adds custom claims to the token and includes additional user data in the response.
    Also prevents token issuance for inactive users.
    """

    @classmethod
    def get_token(cls, user):
        """
        Generates JWT token with custom claims:
        - username: user's username
        - email: user's email address

        These claims are included in the token payload and can be used by the frontend
        for display purposes or authorization logic.
        """
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token

    def validate(self, attrs):
        """
        Validates user credentials and adds additional user-related fields
        to the response payload after successful authentication.

        Also checks if the user is active. If not, raises a validation error.
        """
        data = super().validate(attrs)

        if not self.user.is_active:
            raise serializers.ValidationError('User account is disabled.')

        data['user_id'] = self.user.id
        data['username'] = self.user.username
        data['email'] = self.user.email
        return data

class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset email.

    Attributes:
        email (str): User's registered email address.
                     Required field. Validates that the user exists.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """
        Validate that a user with the provided email exists.

        Args:
            value (str): Email address to validate.

        Returns:
            str: Validated email.

        Raises:
            serializers.ValidationError: If no user with this email exists.
        """
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email was not found.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming and completing the password reset.

    Attributes:
        uid (str): Base64 encoded user ID.
        token (str): Password reset token.
        new_password (str): New password to set. Must meet validation requirements.
    """
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)

    def validate_uid(self, value):
        """
        Validate and decode the UID, checking user existence.

        Args:
            value (str): Base64 encoded UID.

        Returns:
            str: Validated UID.

        Raises:
            serializers.ValidationError: If UID is invalid or user does not exist.
        """
        try:
            uid = force_str(urlsafe_base64_decode(value))
            user = User.objects.get(pk=uid)
        except Exception:
            raise serializers.ValidationError("Invalid or corrupted UID.")
        self.context['user'] = user
        return value

    def validate_new_password(self, value):
        """
        Validate the new password with Django's validators and the custom password validator.

        Args:
            value (str): New password.

        Returns:
            str: Validated password.

        Raises:
            serializers.ValidationError: If the password fails validation.
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """
        Perform cross-field validation for the serializer.

        Checks if the user exists in the serializer context and verifies
        that the provided password reset token is valid for that user.

        Args:
            attrs (dict): The validated data from individual field validators.

        Raises:
            serializers.ValidationError: If the user is not found or the token is invalid or expired.

        Returns:
            dict: The validated data if all checks pass.
        """
        user = self.context.get('user')
        token = attrs.get('token')

        if not user:
            raise serializers.ValidationError({"uid": "User not found."})

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({"token": "Invalid token or token has expired."})

        return attrs
from django.contrib.auth import get_user_model
from rest_framework import serializers
from users.validators import CustomPasswordValidator

User = get_user_model()
custom_password_validator = CustomPasswordValidator()


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

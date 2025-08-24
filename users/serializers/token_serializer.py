from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.validators import CustomPasswordValidator

User = get_user_model()
custom_password_validator = CustomPasswordValidator()


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
        token['email'] = user.email
        token['user_id'] = user.user_id
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

        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['user_id'] = self.user.user_id
        data['email'] = self.user.email
        return data

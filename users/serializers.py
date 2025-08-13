from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer, UserSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.core.validators import validate_email, RegexValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from users.models import UserRole 

User = get_user_model()


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

        data['user_id'] = self.user.user_id
        data['email'] = self.user.email
        return data

class CustomUserCreateSerializer(serializers.ModelSerializer):
    """
    Custom user registration serializer that handles user creation with role assignment.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[
            RegexValidator(
                regex=r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$',
                message='Password must be at least 8 characters long and contain at least one letter and one number.'
            )
        ]
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
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, data):
        """Validate the entire user data."""
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
            
        try:
            validate_email(data.get('email'))
        except ValidationError:
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
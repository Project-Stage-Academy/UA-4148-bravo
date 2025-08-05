from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model
from djoser.serializers import PasswordResetConfirmSerializer as BasePasswordResetConfirmSerializer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

User = get_user_model()

class CustomUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email') 


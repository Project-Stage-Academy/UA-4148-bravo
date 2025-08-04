from djoser.serializers import UserSerializer
from django.contrib.auth import get_user_model
from djoser.serializers import PasswordResetConfirmSerializer as BasePasswordResetConfirmSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()

class CustomUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email') 

class PasswordResetConfirmSerializer(BasePasswordResetConfirmSerializer):

    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        validate_password(value, self.context['user']) # activate all validators from settings.py
        return value
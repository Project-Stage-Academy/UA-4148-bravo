import logging
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.shortcuts import reverse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from djoser.email import PasswordResetEmail

from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    CustomUserCreateSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer
)

logger = logging.getLogger(__name__)


class RegisterThrottle(AnonRateThrottle):
    """Rate limiting for registration endpoint."""
    rate = '5/hour'


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom view for obtaining JWT tokens."""
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(APIView):
    """Handle user registration with email verification."""
    permission_classes = [AllowAny]
    serializer_class = CustomUserCreateSerializer
    throttle_classes = [RegisterThrottle]

    def _generate_verification_token(self):
        return secrets.token_urlsafe(32)

    def _send_verification_email(self, request, user, token):
        verification_relative_url = reverse('verify-email', kwargs={'user_id': user.user_id, 'token': token})
        verification_url = f"{request.scheme}://{request.get_host()}{verification_relative_url}"

        context = {'user': user, 'verification_url': verification_url}
        subject = 'Verify Your Email'
        html_message = render_to_string('email/activation.html', context)
        plain_message = f"Please verify your email by visiting: {verification_url}"

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'status': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            token = self._generate_verification_token()
            user.email_verification_token = token
            user.email_verification_sent_at = timezone.now()
            user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
            self._send_verification_email(request, user, token)
            return Response({
                'status': 'success',
                'message': 'Registration successful! Please check your email to verify your account.',
                'user_id': user.user_id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}", exc_info=True)
            return Response({'status': 'error', 'message': 'Registration failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyEmailView(APIView):
    """Handle email verification."""
    permission_classes = [AllowAny]

    def get(self, request, user_id, token):
        try:
            user = User.objects.get(user_id=user_id, is_active=False, email_verification_token=token)
            if not user.email_verification_sent_at or (timezone.now() - user.email_verification_sent_at) > timedelta(hours=24):
                return Response({'status': 'error', 'message': 'Verification link has expired.'}, status=status.HTTP_400_BAD_REQUEST)

            user.is_active = True
            user.email_verification_token = None
            user.email_verification_sent_at = None
            user.save(update_fields=['is_active', 'email_verification_token', 'email_verification_sent_at'])
            return Response({'status': 'success', 'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'status': 'error', 'message': 'Invalid verification link.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error during email verification: {str(e)}", exc_info=True)
            return Response({'status': 'error', 'message': 'Verification failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def error_response(message, status_code):
    if isinstance(message, str):
        data = {"detail": message}
    else:
        data = message
    return Response(data, status=status_code)


class CustomPasswordResetView(APIView):
    """Handle password reset requests."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response({"email": "User with this email was not found."}, status.HTTP_404_NOT_FOUND)

        PasswordResetEmail(request, {"user": user}).send([user.email])
        return Response({"detail": "Password reset instructions sent."}, status=status.HTTP_200_OK)


class CustomPasswordResetConfirmView(APIView):
    """Confirm password reset with token."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        user = serializer.context['user']
        new_password = serializer.validated_data['new_password']

        try:
            validate_password(new_password, user)
        except Exception as e:
            return error_response({"new_password": list(e.messages)}, status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)


class TokenBlacklistView(APIView):
    """Logout by blacklisting refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Token successfully blacklisted."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to blacklist token."}, status=status.HTTP_400_BAD_REQUEST)

import logging
import secrets
from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.shortcuts import render, reverse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User, UserRole
from .serializers import CustomTokenObtainPairSerializer, CustomUserCreateSerializer

logger = logging.getLogger(__name__)

class RegisterThrottle(AnonRateThrottle):
    """Rate limiting for registration endpoint."""
    rate = '5/hour'

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining JWT tokens.
    Uses CustomTokenObtainPairSerializer for token generation.
    """
    serializer_class = CustomTokenObtainPairSerializer

class UserRegistrationView(APIView):
    """
    Handle user registration with email verification.
    """
    permission_classes = [AllowAny]
    serializer_class = CustomUserCreateSerializer
    throttle_classes = [RegisterThrottle]

    def _generate_verification_token(self):
        """Generate a secure random token for email verification."""
        return secrets.token_urlsafe(32)
    
    def _send_verification_email(self, request, user, token):
        """Send verification email to the user."""
        verification_relative_url = reverse('verify-email', kwargs={'user_id': user.user_id, 'token': token})
        verification_url = f"{request.scheme}://{request.get_host()}{verification_relative_url}"
        
        context = {
            'user': user,
            'verification_url': verification_url,
        }

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
        """
        Handle user registration request.
        """
        logger.info("Received user registration request")
        serializer = self.serializer_class(data=request.data, context={'request': request})
    
        if not serializer.is_valid():
            logger.warning(f"Validation failed: {serializer.errors}")
            return Response(
                {'status': 'error', 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = serializer.save()
            verification_token = self._generate_verification_token()
            user.email_verification_token = verification_token
            user.email_verification_sent_at = timezone.now()
            user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
            
            logger.info(f"User {user.email} registered successfully")

            if not self._send_verification_email(request, user, verification_token):
                logger.error(f"Failed to send verification email to {user.email}")
            
            return Response(
                {
                    'status': 'success',
                    'message': 'Registration successful! Please check your email to verify your account.',
                    'user_id': user.user_id,
                    'email': user.email
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"Error during user registration: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'message': 'An unexpected error occurred during registration.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifyEmailView(APIView):
    """Handle email verification."""
    permission_classes = [AllowAny]

    def get(self, request, user_id, token):
        """Handle email verification link."""
        try:
            user = User.objects.get(
                user_id=user_id,
                is_active=False,
                email_verification_token=token
            )
            
            # Check if token is expired (24 hours)
            token_expired = (
                user.email_verification_sent_at is None or
                (timezone.now() - user.email_verification_sent_at) > timedelta(hours=24)
            )
            
            if token_expired:
                logger.warning(f"Expired verification token for user {user.email}")
                return Response(
                    {'status': 'error', 'message': 'Verification link has expired.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.is_active = True
            user.email_verification_token = None
            user.email_verification_sent_at = None
            user.save(update_fields=['is_active', 'email_verification_token', 'email_verification_sent_at'])
            
            logger.info(f"User {user.email} email verified successfully")
            return Response(
                {'status': 'success', 'message': 'Email verified successfully. You can now log in.'},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            logger.warning(f"Invalid verification attempt with user_id: {user_id}")
            return Response(
                {'status': 'error', 'message': 'Invalid verification link.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Error during email verification: {str(e)}", exc_info=True)
            return Response(
                {'status': 'error', 'message': 'An error occurred during verification.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
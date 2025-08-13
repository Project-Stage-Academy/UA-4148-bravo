import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from djoser.email import PasswordResetEmail
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from .serializers import PasswordResetSerializer, PasswordResetConfirmSerializer

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
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .serializers import ResendEmailSerializer
from .tokens import email_verification_token

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
            
            if user.is_active:
                return Response(
                    {'status': 'success', 'message': 'Email is already verified.'},
                    status=status.HTTP_200_OK
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
            
            if user.pending_email:
                user.email = user.pending_email
                user.pending_email = None
            
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

class ResendEmailView(APIView):
    """
    API view to resend the email verification link.

    This view allows users to request a new verification email to be sent to their
    registered or pending email address. It supports optional updating of the pending email
    and token generation. The response does not disclose whether the user exists
    for security reasons.

    Attributes:
        permission_classes (list): List of permission classes allowing unrestricted access.
        throttle_scope (str): Named scope for rate limiting resend email requests.
        throttle_classes (list): List of throttling classes applied to the view.
    """
    permission_classes = [AllowAny]
    throttle_scope = "resend_email"
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        """
        Handle POST request to resend the email verification link.

        Validates the input data, retrieves the user by user_id, updates the pending email if provided,
        generates a new token if not supplied, constructs the verification URL, renders
        email templates (HTML and plain text), sends the email, and returns a generic
        success response regardless of whether the user exists.

        Args:
            request (Request): DRF request object containing user_id (required), 
                optional email (new pending email), and optional token.

        Returns:
            Response: DRF Response object with HTTP 202 Accepted status and a message
                indicating that if the account exists, a verification email has been sent.
        """
        serializer = ResendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data["user_id"]
        email = serializer.validated_data.get("email")
        token = serializer.validated_data.get("token")

        try:
            user = User.objects.get(user_id=user_id)
            if user.is_active:
                return Response(
                    {"detail": "If the account exists, a verification email has been sent."},
                    status=status.HTTP_202_ACCEPTED,
                )

        except User.DoesNotExist:
            return Response(
                {"detail": "If the account exists, a verification email has been sent."},
                status=status.HTTP_202_ACCEPTED,
            )

        if email:
            user.pending_email = email
            user.save(update_fields=["pending_email"])
        else:
            email = user.pending_email or user.email

        if not token:
            token = email_verification_token.make_token(user)

        verification_relative_url = reverse(
            'verify-email', kwargs={'user_id': user.user_id, 'token': token}
        )
        verify_url = f"{settings.FRONTEND_URL}{verification_relative_url}?email={email}"

        context = {
            'user': user,
            'verification_url': verify_url,
            'user_display_name': user.first_name or user.email,
            'support_text': "If you didn't request this, please ignore this email.",
        }

        subject = "Confirm your email"
        html_message = render_to_string('email/activation.html', context)
        plain_message = (
            f"Hello {context['user_display_name']},\n\n"
            f"Please verify your email by clicking the link below:\n{verify_url}\n\n"
            f"{context['support_text']}"
        )

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")

        return Response(
            {"detail": "If the account exists, a verification email has been sent."},
            status=status.HTTP_202_ACCEPTED,
        )

def error_response(message, status_code):
    """
    Helper to return error responses in consistent format.

    Args:
        message (str or dict): Error message or dict of errors.
        status_code (int): HTTP status code.

    Returns:
        Response: DRF Response with given message and status.
    """
    if isinstance(message, str):
        data = {"detail": message}
    else:
        data = message
    return Response(data, status=status_code)

class CustomPasswordResetView(APIView):
    """
    Handle password reset requests by sending reset instructions via email.

    Methods:
        post: Accepts an email and sends password reset instructions if the user exists.

    Args in post:
        request (Request): The HTTP request object containing POST data.

    Returns:
        Response: DRF Response with success message or error details.
    """
    def post(self, request, *args, **kwargs):
        """
        Process password reset request.

        Args:
            request (Request): HTTP request with 'email' in data.

        Returns:
            Response: 
                - 200 OK with success detail if email sent.
                - 400 Bad Request if email is missing.
                - 404 Not Found if user with email doesn't exist.
        """
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response({"email": "User with this email was not found."}, status.HTTP_404_NOT_FOUND)

        context = {"user": user}
        to = [getattr(user, User.EMAIL_FIELD)]
        PasswordResetEmail(request, context).send(to)

        return Response({"detail": "Password reset instructions have been sent to the provided email."}, status=status.HTTP_200_OK)


class CustomPasswordResetConfirmView(APIView):
    """
    Handle confirmation of password reset using UID and token.

    Methods:
        post: Validates token and new password, updates the user password.

    Args in post:
        request (Request): The HTTP request object containing 'uid', 'token', and 'new_password'.

    Returns:
        Response:
            - 200 OK if password changed successfully.
            - 400 Bad Request for missing fields, invalid token, invalid UID, or invalid password.
    """
    def post(self, request, *args, **kwargs):
        """
        Process password reset confirmation.

        Args:
            request (Request): HTTP request with 'uid', 'token', 'new_password' in data.

        Returns:
            Response:
                - 200 OK with success detail if password updated.
                - 400 Bad Request if any validation fails.
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        user = serializer.context['user']
        new_password = serializer.validated_data['new_password']

        try:
            validate_password(new_password, user)
        except DjangoValidationError as e:
            return error_response({"new_password": list(e.messages)}, status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password has been successfully changed."}, status=status.HTTP_200_OK)

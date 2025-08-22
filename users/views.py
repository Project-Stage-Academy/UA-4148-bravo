# Python standard library
import logging
import secrets
from datetime import timedelta
from smtplib import SMTPException
from urllib.parse import urljoin

# Django imports
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import (
    ObjectDoesNotExist,
    ValidationError as DjangoValidationError,
    ImproperlyConfigured,
)
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import render, reverse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import (
    urlsafe_base64_decode,
    urlsafe_base64_encode,
)

# Third-party imports
import requests
from djoser.email import PasswordResetEmail
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import (
    TokenRefreshView as SimpleJWTRefreshView,
    TokenBlacklistView as SimpleJWTBlacklistView,
)
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

# Local application imports
from .constants import (
    ACTIVATION_EMAIL_TEMPLATE,
    SUPPORT_TEXT,
    EMAIL_VERIFICATION_TOKEN,
)
from .models import User, UserRole
from .serializers import (
    CustomTokenObtainPairSerializer,
    CustomUserCreateSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    ResendEmailSerializer,
    UserSerializer,
)

from drf_spectacular.utils import extend_schema, OpenApiResponse
from .serializers import CurrentUserSerializer
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)

class RegisterThrottle(AnonRateThrottle):
    """Rate limiting for registration endpoint."""
    rate = '5/hour'

@extend_schema(
    tags=["Auth"],
    summary="Obtain JWT access/refresh tokens",
    request=CustomTokenObtainPairSerializer,
    responses={
        200: CustomTokenObtainPairSerializer,
        401: OpenApiResponse(description="Invalid credentials"),
    },
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining JWT tokens.
    Uses CustomTokenObtainPairSerializer for token generation.
    """
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=["Auth"],
    summary="Refresh JWT access token",
)
class JWTRefreshView(SimpleJWTRefreshView):
    pass


@extend_schema(
    tags=["Auth"],
    summary="Logout (blacklist refresh token)",
)
class JWTLogoutView(SimpleJWTBlacklistView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return Response({"detail": "Successfully logged out."}, status=response.status_code)

@extend_schema(
    tags=["Auth"],
    summary="Register a new user",
    request=CustomUserCreateSerializer,
    responses={
        201: OpenApiResponse(description="User created and verification email sent"),
        400: OpenApiResponse(description="Validation errors"),
    },
)
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
        verification_relative_url = settings.FRONTEND_ROUTES["verify_email"].format(
            user_id=user.user_id,
            token=token,
        )
        verification_url = urljoin(settings.FRONTEND_URL, verification_relative_url)
        
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
                status=status.HTTP_409_CONFLICT
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

@extend_schema(
    tags=["Auth"],
    summary="Verify email address",
    responses={
        200: OpenApiResponse(description="Email verified"),
        400: OpenApiResponse(description="Invalid or expired verification link"),
    },
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
            
            if user.pending_email:
                try:
                    user.confirm_pending_email()
                except DjangoValidationError as e:
                    if getattr(e, "code", None) == "no_pending_email":
                        logger.info(f"No pending email to confirm for {user.email}") 
                        return Response(
                            {'status': 'success', 'message': 'Email is already verified.'},
                            status=status.HTTP_200_OK
                        )
                    else:
                        logger.warning(f"Failed to confirm pending email for {user.email}: {e}")         
                        return Response(
                            {"status": "error", "message": str(e)},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            else:
                user.is_active = True
            
            user.email_verification_token = None
            user.email_verification_sent_at = None
            user.save(update_fields=['is_active', 'email', 'email_verification_token', 'email_verification_sent_at'])
            
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

@extend_schema(
    tags=["Auth"],
    summary="Resend verification email",
    request=ResendEmailSerializer,
    responses={
        202: OpenApiResponse(description="If the account exists, a verification email has been sent"),
        400: OpenApiResponse(description="Missing or invalid data"),
    },
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
    serializer_class = ResendEmailSerializer

    def post(self, request):
        """
        Resend the email verification link to a user's email address.

        This view validates the input data, retrieves the user by `user_id`,
        updates the `pending_email` if a new one is provided, generates a new
        verification token if not supplied, constructs the verification URL,
        renders HTML and plain text email chat, sends the email, and returns
        a generic success response regardless of whether the user exists.

        The email is sent to `pending_email` if it exists; otherwise, the user's
        primary email is used. The response does not disclose whether the user
        exists for security reasons.

        Args:
            request (rest_framework.request.Request): DRF request object containing:
                - user_id (int): Required ID of the user.
                - email (str, optional): New pending email to update.
                - token (str, optional): Custom verification token to use.

        Returns:
            rest_framework.response.Response: HTTP 202 Accepted with a generic
            message indicating that if the account exists, a verification email
            has been sent.
        """
        serializer = ResendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data["user_id"]
        new_email = serializer.validated_data.get("email")
        token = serializer.validated_data.get("token")

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "If the account exists, a verification email has been sent."},
                status=status.HTTP_202_ACCEPTED,
            )

        if new_email:
            normalized_email = new_email.strip().lower()
            user.pending_email = normalized_email
            
            try:
                user.save(update_fields=["pending_email"])
            except IntegrityError:
                logger.warning(f"Failed to update pending_email for user {user.user_id}: email already exists")
                
        email_to_send = user.pending_email or user.email
        if not email_to_send:
            logger.warning(f"User {user.user_id} has no valid email to send verification to.")
            return Response(
                {"detail": "Unable to send verification email due to missing email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token:
            token = EMAIL_VERIFICATION_TOKEN.make_token(user)

        verification_url = settings.FRONTEND_ROUTES["verify_email"].format(
            user_id=user.user_id,
            token=token,
        )
        verify_url = urljoin(settings.FRONTEND_URL, verification_url)

        context = {
            'user': user,
            'verification_url': verify_url,
            'user_display_name': user.first_name or user.email,
            'support_text': SUPPORT_TEXT,
        }

        subject = "Confirm your email"
        html_message = render_to_string(ACTIVATION_EMAIL_TEMPLATE, context)
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
                recipient_list=[email_to_send],
                html_message=html_message,
                fail_silently=False,
            )
        except (ImproperlyConfigured, SMTPException) as e:
            logger.critical(
                f"Verification email send failed to {email_to_send}",
                exc_info=True
            )
            return Response(
                {"detail": "Internal server configuration error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(
                f"Verification email send failed to {email_to_send}: {e}",
                exc_info=True
            )
            return Response(
                {"detail": "If the account exists, a verification email has been sent."},
                status=status.HTTP_202_ACCEPTED,
            )      

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

@extend_schema(
    tags=["Auth"],
    summary="Request password reset",
    request=PasswordResetSerializer,
    responses={
        200: OpenApiResponse(description="Password reset email sent"),
        400: OpenApiResponse(description="Validation error"),
        404: OpenApiResponse(description="User not found"),
    },
)
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
    serializer_class = PasswordResetSerializer
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

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_relative_url = settings.FRONTEND_ROUTES["reset_password"].format(
            uid=uid,
            token=token,
        )
        reset_url = urljoin(settings.FRONTEND_URL, reset_relative_url)

        subject = "Reset your password"
        context = {
            "user": user,
            "reset_url": reset_url,
        }
        html_message = render_to_string("email/password_reset.html", context)
        plain_message = f"Use this link to reset your password: {reset_url}"

        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
        )

        return Response({"detail": "Password reset instructions have been sent to the provided email."}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Auth"],
    summary="Confirm password reset",
    request=PasswordResetConfirmSerializer,
    responses={
        200: OpenApiResponse(description="Password changed successfully"),
        400: OpenApiResponse(description="Invalid token, UID, or password"),
    },
)
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
    serializer_class = PasswordResetConfirmSerializer
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


User = get_user_model()
def get_default_user_role():
    """
    Retrieve the default 'user' role with caching and error handling.
    
    Returns:
        UserRole: The default user role object
        
    Raises:
        RuntimeError: If the default user role is not configured in the system
    """
    cache_key = "default_user_role"
    default_role = cache.get(cache_key)
    
    if default_role is None:
        try:
            default_role = UserRole.objects.get(role="user")
            cache.set(cache_key, default_role, timeout=3600)  # Cache for 1 hour
        except UserRole.DoesNotExist:
            raise RuntimeError(
                "Default 'user' role is not configured in the system. "
                "Please create a UserRole with role='user'."
            )
    
    return default_role

@extend_schema(
    tags=["Auth"],
    summary="Login with OAuth provider to obtain JWT",
    responses={
        200: CustomTokenObtainPairSerializer,
        400: OpenApiResponse(description="Invalid request or provider token"),
        403: OpenApiResponse(description="Email not provided/verified by provider"),
    },
)
class OAuthTokenObtainPairView(TokenObtainPairView):
    """
    Extended token authentication endpoint that supports both traditional email/password
    and OAuth provider authentication (Google/GitHub).
    
    Inherits from Djoser's TokenObtainPairView to maintain all standard functionality
    while adding OAuth support through a unified authentication endpoint.
    
    Endpoint: users/oauth/login/
    Methods: POST
    
    Request Formats:
        - OAuth: {"provider": "google|github", "access_token": "oauth_token"}
        - Password: {"email": "user@example.com", "password": "password123"}
    """
    
    permission_classes = [AllowAny]  # Explicitly mark as public endpoint
    throttle_classes = [AnonRateThrottle]  # Prevent brute-force attacks

    def post(self, request, *args, **kwargs):
        """
        Handle authentication requests, routing to appropriate method based on input.
        
        Args:
            request: DRF request object containing authentication credentials
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Response: JSON containing either:
                - JWT tokens and user data (success)
                - Error message (failure)
                
        Status Codes:
            - 200 OK: Successful authentication
            - 400 Bad Request: Missing/invalid parameters
            - 401 Unauthorized: Invalid credentials
        """
        # Check if this is an OAuth request
        provider = request.data.get('provider') # 'google' or 'github'
        access_token = request.data.get('access_token')
        
        if provider and access_token:
            if isinstance(provider, str) and isinstance(access_token, str):
                provider = provider.lower().strip()  # Normalize provider
                return self.handle_oauth(provider, access_token)
            else:
                return Response(
                {"error": "Invalid provider or access_token type"},
                status=status.HTTP_400_BAD_REQUEST
                ) 
        else:
            return Response(
                {"error": "Provider or Access_token is missing"},
                status=status.HTTP_400_BAD_REQUEST
                ) 
    def handle_oauth(self, provider, access_token):
        """
        Route OAuth authentication requests to the appropriate provider handler.
        
        Args:
            provider: String identifying the OAuth provider ('google' or 'github')
            access_token: Valid OAuth access token from the provider
            
        Returns:
            Response: JSON response from the provider handler or error if unsupported
            
        Raises:
            HTTP 400: If provider is not supported
        """
        if provider == 'google':
            return self.handle_google_oauth(access_token)
        elif provider == 'github':
            return self.handle_github_oauth(access_token)
        else:
            return Response(
                {"error": "Unsupported OAuth provider"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def handle_google_oauth(self, access_token):
        """
        Authenticate using Google OAuth access token.
        
        1. Validates token with Google's API
        2. Retrieves user profile information
        3. Creates/updates local user record
        4. Issues JWT tokens
        
        Args:
            access_token: Valid Google OAuth access token
            
        Returns:
            Response: JSON containing JWT tokens and user data or error message
            
        Status Codes:
            - 200 OK: Successful authentication
            - 400 Bad Request: Invalid token or missing email
            - 408 Request Timeout: Google API timeout
            - 502 Bad Gateway: Network issues with Google API
        """
        google_userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(google_userinfo_url, headers=headers, timeout=(3.05, 10))
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.Timeout as e:
            logger.error(
                "Google OAuth timeout",
                extra={
                    'error_type': 'timeout',
                    'timeout': str(e),
                    'provider': 'google'
                }
            )
            return Response(
                {
                    "error": "Google API timeout",
                    "detail": "The connection to Google's servers timed out",
                    "resolution": "Please try again later"
                },
                status=status.HTTP_408_REQUEST_TIMEOUT
            )
        
        except requests.exceptions.SSLError:
            logger.error("Google OAuth SSL verification failed")
            return Response(
                {
                    "error": "Security verification failed",
                    "detail": "Could not establish secure connection to Google",
                    "resolution": "Try again or contact support"
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
        
        except requests.exceptions.ConnectionError:
            logger.error("Google OAuth connection failed")
            return Response(
                {
                    "error": "Connection failed",
                    "detail": "Network issues contacting Google's servers",
                    "resolution": "Check your internet connection"
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
        
        except requests.exceptions.RequestException as e:
            response_data = {}
            if hasattr(e, 'response'):
                try:
                    response_data = e.response.json()
                except ValueError:
                    response_data = {'raw_response': str(e.response.content)}
            
            logger.error(
                "Google OAuth token validation failed",
                extra={
                    'error_type': 'token_validation',
                    'http_status': getattr(e.response, 'status_code', None),
                    'response': response_data,
                    'provider': 'google'
                }
            )
        
            return Response(
                {
                    "error": "Invalid Google token",
                    "detail": "The provided access token was rejected by Google",
                    "resolution": "Re-authenticate with Google"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        if not isinstance(data, dict):
            return Response(
            {"error": f"Expected JSON object, got {type(data).__name__}"},
            status=status.HTTP_400_BAD_REQUEST
        )
        
        email = data.get("email")
        if not email:
            return Response(
                {
                    "error": (
                        "Email not provided by OAuth provider. "
                        "This may be due to the provider not sharing it or the user's privacy settings. "
                        "Ensure email access is requested in the provider's scope."
                    )
                }, 
                status=status.HTTP_400_BAD_REQUEST
            )

        first_name = data.get("given_name", "")
        last_name = data.get("family_name", "")

        user, _ = self.get_or_create_user(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "password": "",
                "user_phone": "",
                "title": "",
                "role": get_default_user_role()
            },
            provider = "google"
        )

        return self.generate_jwt_response(user)
    
    def handle_github_oauth(self, access_token):
        """
        Authenticate using GitHub OAuth access token.
        
        1. Validates token with GitHub's API
        2. Retrieves user profile and primary email
        3. Creates/updates local user record
        4. Issues JWT tokens
        
        Args:
            access_token: Valid GitHub OAuth access token
            
        Returns:
            Response: JSON containing JWT tokens and user data or error message
            
        Status Codes:
            - 200 OK: Successful authentication
            - 400 Bad Request: Invalid token or missing email
            - 403 Forbidden: Email not visible (privacy)
            - 408 Timeout: GitHub API timeout
            - 502 Bad Gateway: Network issues
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        try:
            # Get user info
            user_response = requests.get(
                "https://api.github.com/user", 
                headers=headers,
                timeout=(3.05, 10)
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Get emails (separate endpoint)
            email_response = requests.get(
                "https://api.github.com/user/emails", 
                headers=headers,
                timeout=(3.05, 5)
            )
            email_response.raise_for_status()
            emails = email_response.json()

            primary_email = next(
                (e for e in emails if e.get("primary")), 
                None
            )

            
            if not primary_email:
                logger.warning(
                    "GitHub OAuth missing verified primary email",
                    extra={
                        'available_emails': [
                            {'email': e['email'], 'verified': e['verified']}
                            for e in emails if 'email' in e
                            ],
                        'github_id': user_data.get('id')
                    }
                )
                return Response(
                    {
                        "error": "Email not provided by GitHub",
                        "detail": (
                            "No verified primary email found on GitHub account. "
                            "Users must have a verified primary email to authenticate."
                        ),
                        "resolution": [
                            "1. Check email settings at: https://github.com/settings/emails",
                            "2. Verify at least one email address",
                            "3. Set one as primary"
                        ],
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            email = primary_email['email']
    
            # Process name
            full_name = user_data.get("name", "").strip()
            name_parts = full_name.split(" ", 1)
            first_name = name_parts[0][:150] if name_parts else "" 
            last_name = name_parts[1][:150] if len(name_parts) > 1 else ""

            user, _ = self.get_or_create_user(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "password": "",
                    "user_phone": "",
                    "title": "",
                    "role": get_default_user_role()
                },
                provider = "github"
            )

            return self.generate_jwt_response(user)
            
        except requests.Timeout:
            logger.error("GitHub API timeout")
            return Response(
                {
                    "error": "GitHub API timeout",
                    "detail": "Connection to GitHub servers timed out",
                    "resolution": "Please try again later"
                },
                status=status.HTTP_408_REQUEST_TIMEOUT
            )
        
        except requests.ConnectionError:
            logger.error("GitHub connection failed")
            return Response(
                {
                    "error": "Network error",
                    "detail": "Could not reach GitHub servers",
                    "resolution": "Check your internet connection"
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
        
        except requests.HTTPError as e:
            error_data = {}
            try:
                error_data = e.response.json()
            except ValueError:
                error_data = {'raw_response': str(e.response.content)}
            
            logger.error(
                "GitHub API error",
                extra={
                    'status_code': e.response.status_code,
                    'error': error_data.get('message'),
                    'github_docs': error_data.get('documentation_url')
                }
            )
        
            if e.response.status_code == 401:
                return Response(
                    {
                        "error": "Invalid GitHub token",
                        "detail": "The access token was rejected",
                        "resolution": "Re-authenticate with GitHub"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {
                        "error": "GitHub API error",
                        "detail": error_data.get('message', 'Unknown error'),
                        "documentation": error_data.get('documentation_url')
                    },
                    status=status.HTTP_502_BAD_GATEWAY
                )
            
        except Exception as e:
            logger.critical(
                "Unexpected GitHub OAuth error",
                exc_info=True,
                extra={'error': str(e)}
            )
            return Response(
                {
                    "error": "Authentication processing failed",
                    "detail": "An unexpected error occurred",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_or_create_user(self, email, defaults, provider):
        """
        Helper method to get or create user with intelligent field updates.
        
        Args:
            email: User's email address (primary lookup key)
            defaults: Dictionary of default values for new user creation
            
        Returns:
            tuple: (user_object, created_bool) where:
                - user_object: The retrieved or created user instance
                - created_bool: Boolean indicating if user was created
        """
        from users.tasks import send_welcome_oauth_email_task
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults=defaults
        )
        
        if created:
            user.set_unusable_password()
            user.save()
            logger.info(
                f"User created via {provider} OAuth",
                extra={
                'user_id': user.pk,
                'email': email,
                'provider': provider,
                'action': 'user_creation',
                'source': 'oauth',
                'fields_created': {
                    'first_name': defaults["first_name"],
                    'last_name': defaults["last_name"],
                    'role': user.role.role if user.role else None
                    }
                }
            )
        else:
            # If user exists, their first_name and last_name are updated with values from provider, while role stays unchanged
            update_fields = {}
            if defaults.get('first_name'):
                update_fields['first_name'] = defaults['first_name']
            if defaults.get('last_name'):
                update_fields['last_name'] = defaults['last_name']
            
            if update_fields:
                User.objects.filter(pk=user.pk).update(**update_fields)
                user.refresh_from_db()
                logger.info(
                    "User logged in via OAuth",
                    extra={
                        'user_id': user.pk,
                        'email': email,
                        'provider': provider,
                        'action': 'user_update',
                        'source': 'oauth',
                        'fields_updated': update_fields,
                        'changed_fields': list(update_fields.keys())
                    }
                )
        PROVIDER_MAP = {
            "google": "Google",
            "github": "GitHub",
        }

        provider_name = PROVIDER_MAP.get(provider.lower(), provider)
        subject="Welcome to Forum — your space for innovation!"
        message = render_to_string(
            "email/welcome_oauth_email.txt",
            {"action": "registered" if created else "logged in", "provider_name": provider_name},
        )
        send_welcome_oauth_email_task.delay(
            subject=subject,
            message=message,
            recipient_list=[email],
        )
        return user, created
    
    def generate_jwt_response(self, user):
        """
        Generate standardized JWT token response with user data.
        
        Args:
            user: Authenticated user instance
            
        Returns:
            Response: DRF Response object containing:
                - refresh: JWT refresh token
                - access: JWT access token
                - user: Serialized user data
        """
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        })    

@extend_schema(
    operation_id="auth_me",
    summary="Retrieve the currently authenticated user",
    description=(
        "Returns the profile information of the currently authenticated user. "
        "Requires a valid JWT access token. "
        "If the token is missing or invalid, returns 401 Unauthorized."
    ),
    responses={
        200: CurrentUserSerializer,
        401: OpenApiResponse(description="Unauthorized - missing or invalid token"),
        403: OpenApiResponse(description="Forbidden - user account is inactive"),
        404: OpenApiResponse(description="Not Found - user no longer exists"),
    },
    tags=["Auth"],
)
class MeView(APIView):
    """Returns profile info of the currently authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data)


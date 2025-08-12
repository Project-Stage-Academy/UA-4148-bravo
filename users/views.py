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
from .serializers import CustomTokenObtainPairSerializer
import requests

from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
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


User = get_user_model()
def get_default_role():
    return UserRole.objects.get(role="user")

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
        provider = request.data.get('provider')  # 'google' or 'github'
        access_token = request.data.get('access_token')
        
        if provider and access_token:
            return self.handle_oauth(provider, access_token)
        
        # Fall back to standard email/password auth
        return super().post(request, *args, **kwargs)
    
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
        """
        google_userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(google_userinfo_url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            return Response(
                {"error": "Invalid Google token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = data.get("email")
        if not email:
            return Response(
                {"error": "Email not provided"}, 
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
                "role": get_default_role()
            }
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
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        try:
            # Get user info
            user_response = requests.get(
                "https://api.github.com/user", 
                headers=headers
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Get email (might need separate request)
            email = user_data.get("email")
            if not email:
                email_response = requests.get(
                    "https://api.github.com/user/emails", 
                    headers=headers
                )
                email_response.raise_for_status()
                emails = email_response.json()
                primary_email = next(
                    (e for e in emails if e.get("primary")), 
                    None
                )
                if primary_email:
                    email = primary_email.get("email")

            if not email:
                return Response(
                    {"error": "Email not provided by GitHub"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Process name
            username = user_data.get("login")
            name_parts = user_data.get("name", "").split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            user, _ = self.get_or_create_user(
                email=email,
                defaults={
                    # "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "password": "",
                    "user_phone": "",
                    "title": "",
                    "role": get_default_role()
                }
            )

            return self.generate_jwt_response(user)
            
        except requests.RequestException:
            return Response(
                {"error": "Invalid GitHub token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get_or_create_user(self, email, defaults):
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
        user, created = User.objects.get_or_create(
            email=email,
            defaults=defaults
        )
        
        if created:
            user.set_unusable_password()
            user.save()
        else:
            update_fields = {}
            if not user.first_name and defaults.get('first_name'):
                update_fields['first_name'] = defaults['first_name']
            if not user.last_name and defaults.get('last_name'):
                update_fields['last_name'] = defaults['last_name']
            
            if update_fields:
                User.objects.filter(pk=user.pk).update(**update_fields)
                user.refresh_from_db()
        
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
            "user": {
                "id": user.user_id,
                # "username": username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_phone": user.user_phone,
                "title": user.title,
                "role": str(get_default_role())
            }
        })        
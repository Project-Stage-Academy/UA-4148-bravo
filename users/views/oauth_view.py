# Python standard library
import logging

# Third-party imports
import requests

# Django imports
from django.template.loader import render_to_string
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

# Local application imports
from users.models import User
from social_django.utils import load_strategy, load_backend
from users.serializers.token_serializer import CustomTokenObtainPairSerializer
from users.serializers.user_serializers import UserSerializer
from users.tasks import send_welcome_oauth_email_task
from utils.get_default_user_role import get_default_user_role
from utils.cookies import set_auth_cookies

logger = logging.getLogger(__name__)


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
    
    Endpoint: api/v1/auth/oauth/login/
    Methods: POST
    
    Request Formats:
        - OAuth: {"provider": "google|github", "access_token": "oauth_token"}
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

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
        provider = request.data.get("provider")
        access_token = request.data.get("access_token")

        if not isinstance(provider, str) or not provider.strip():
            return Response(
                {"error": "Invalid provider"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not access_token:
            return Response(
                {"error": "access_token is missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        provider = provider.lower().strip()
        if provider not in ["google", "github"]:
            return Response(
                {"error": "Unsupported OAuth provider"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = self.authenticate_with_provider(provider, access_token)
        except Exception as e:
            logger.error("OAuth authentication failed", exc_info=True)
            return Response(
                {"error": "OAuth authentication failed", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return self.generate_jwt_response(user)

    def authenticate_with_provider(self, provider, access_token):
        """
        Authenticate user using social-auth-app-django backend.
        Raises ValueError if token is invalid or expired.
        """
        PROVIDER_BACKEND_MAP = {
            "google": "google-oauth2",
            "github": "github",
        }
        provider_name = PROVIDER_BACKEND_MAP.get(provider)
        strategy = load_strategy()
        backend = load_backend(strategy=strategy, name=provider_name, redirect_uri=None)

        try:
            user = backend.do_auth(access_token)
        except Exception as e:
            logger.error("Backend authentication error", exc_info=True)
            raise ValueError("Invalid or expired token") from e

        if not user:
            raise ValueError("Invalid or expired token")

        if provider == "github" and not getattr(user, "email", None):
            try:
                emails = requests.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"token {access_token}"},
                    timeout=(3.05, 5)
                ).json()
            except Exception as e:
                logger.error("Failed to fetch GitHub emails", exc_info=True)
                raise ValueError("Cannot retrieve email from GitHub") from e

            primary_email = next(
                (e["email"] for e in emails if e.get("primary") and e.get("verified")),
                None
            )
            if not primary_email:
                raise ValueError("Email not provided by GitHub")
            user.email = primary_email
            user.save()

        if not hasattr(user, "role") or user.role is None:
            user.role = get_default_user_role()
            user.save()

        created = strategy.session_get('user_created')
        self.send_welcome_email(user, provider, created)
        return user

    def send_welcome_email(self, user, provider, created):
        """
        Send welcome email after OAuth login/registration.
        """
        PROVIDER_MAP = {"google": "Google", "github": "GitHub"}
        provider_name = PROVIDER_MAP.get(provider, provider)

        action = "registered" if created else "logged in"

        subject = "Welcome to Forum — your space for innovation!"
        message = render_to_string(
            "email/welcome_oauth_email.txt",
            {"action": action, "provider_name": provider_name},
        )
        send_welcome_oauth_email_task.delay(
            subject=subject,
            message=message,
            recipient_list=[user.email],
        )

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
        if not user.is_active:
            return Response(
                {"detail": "Account is not active. Please verify your email."},
                status=403
            )
        
        refresh = RefreshToken.for_user(user)
        refresh_token = str(refresh)
        access = str(refresh.access_token)
        response = Response({
            "user": UserSerializer(user).data
        })
        set_auth_cookies(response, access, refresh_token)
        
        return response

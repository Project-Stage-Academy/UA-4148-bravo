# Python standard library
import logging
import secrets
from urllib.parse import urljoin

# Django imports
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse

# Third-party imports
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

# Local application imports
from users.serializers.user_serializers import ExtendedCurrentUserSerializer
from users.serializers.user_serializers import CustomUserCreateSerializer
from users.views.base_protected_view import CookieJWTProtectedView

logger = logging.getLogger(__name__)


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
    authentication_classes = []
    serializer_class = CustomUserCreateSerializer

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
            if 'email' in serializer.errors and User.objects.filter(
                    email=request.data.get('email')
            ).exists():
                return Response(
                    {'status': 'error', 'errors': serializer.errors},
                    status=status.HTTP_409_CONFLICT
                )
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


User = get_user_model()


@extend_schema(
    operation_id="auth_me",
    summary="Retrieve the currently authenticated user",
    description=(
            "Returns the profile information of the currently authenticated user. "
            "Requires a valid JWT access token. "
            "If the token is missing or invalid, returns 401 Unauthorized."
    ),
    responses={
        200: ExtendedCurrentUserSerializer,
        401: OpenApiResponse(description="Unauthorized - missing or invalid token"),
        403: OpenApiResponse(description="Forbidden - user account is inactive"),
        404: OpenApiResponse(description="Not Found - user no longer exists"),
    },
    tags=["Auth"],
)
class MeView(CookieJWTProtectedView):
    """Returns profile info of the currently authenticated user."""

    def get(self, request):
        serializer = ExtendedCurrentUserSerializer(request.user)
        return Response(serializer.data)

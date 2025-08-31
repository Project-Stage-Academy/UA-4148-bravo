# Python standard library
import logging
from urllib.parse import urljoin
from datetime import timedelta
from smtplib import SMTPException

# Django imports
from django.conf import settings
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
    ImproperlyConfigured,
)
from django.core.mail import send_mail
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse

# Third-party imports
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

# Local application imports
from users.constants import (
    ACTIVATION_EMAIL_TEMPLATE,
    SUPPORT_TEXT,
    EMAIL_VERIFICATION_TOKEN,
)
from users.models import User
from users.serializers.resend_email_serializer import ResendEmailSerializer

logger = logging.getLogger(__name__)


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
    authentication_classes = []

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
    authentication_classes = []
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

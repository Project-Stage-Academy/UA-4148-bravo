# Python standard library
import logging

# Django imports
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from rest_framework.permissions import AllowAny

# Third-party imports
from djoser.email import PasswordResetEmail
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# Local application imports
from users.models import User
from users.serializers.password_reset_serializers import (
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)
from utils.error_response import error_response

logger = logging.getLogger(__name__)


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
    permission_classes = [AllowAny]
    authentication_classes = []
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

        context = {"user": user}
        to = [getattr(user, User.EMAIL_FIELD)]
        PasswordResetEmail(request=request._request, context=context).send(to)

        return Response({"detail": "Password reset instructions have been sent to the provided email."},
                        status=status.HTTP_200_OK)


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
    permission_classes = [AllowAny]
    authentication_classes = []
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

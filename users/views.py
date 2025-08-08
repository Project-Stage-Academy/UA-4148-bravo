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
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

logger = logging.getLogger(__name__)  # Added this

# Custom view to use the custom JWT serializer
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Optional logging setup (can be removed if not needed)
if __name__ == "__main__":
    logger.debug("This is a debug message.")
    logger.info("Informational message.")
    logger.warning("Warning occurred!")
    logger.error("An error happened.")
    logger.critical("Critical issue!")



# Create your views here.

User = get_user_model()

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


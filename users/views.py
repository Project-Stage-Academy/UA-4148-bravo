from django.shortcuts import render
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

logger = logging.getLogger(__name__)

logger.debug("This is a debug message.")
logger.info("Informational message.")
logger.warning("Warning occurred!")
logger.error("An error happened.")
logger.critical("Critical issue!")

# Create your views here.

User = get_user_model()


class CustomPasswordResetView(APIView):
    """
    Request for password reset.
    Sends an email if the user exists and returns clear feedback.
    """
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        if not email:
            return Response({"email": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"email": "User with this email was not found."}, status=status.HTTP_404_NOT_FOUND)

        # Sending email (via standard Djoser email class)
        context = {"user": user}
        to = [getattr(user, User.EMAIL_FIELD)]
        PasswordResetEmail(request, context).send(to)

        return Response({"detail": "Password reset instructions have been sent to the provided email."}, status=status.HTTP_200_OK)


class CustomPasswordResetConfirmView(APIView):
    """
    Confirm password reset.
    Checks the token, expiration time, and validates the new password.
    """
    def post(self, request, *args, **kwargs):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        # Check required fields
        if not uid or not token or not new_password:
            return Response({"detail": "Not all required fields are filled."}, status=status.HTTP_400_BAD_REQUEST)

        # Decode UID and find user
        try:
            uid = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"uid": "Invalid or corrupted UID."}, status=status.HTTP_400_BAD_REQUEST)

        # Check token
        if not default_token_generator.check_token(user, token):
            return Response({"token": "Invalid token or token has expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate password (runs both standard and custom validators)
        try:
            validate_password(new_password, user)
        except DjangoValidationError as e:
            return Response({"new_password": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        # Save new password
        user.set_password(new_password)
        user.save()

        return Response({"detail": "Password has been successfully changed."}, status=status.HTTP_200_OK)



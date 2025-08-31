from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from users.models import User
import logging
from validation.validate_token import safe_decode

logger = logging.getLogger(__name__)

class CookieJWTAuthentication(BaseAuthentication):
    """
    Custom DRF authentication class that reads the JWT access token from an HttpOnly cookie.

    Always returns 401 Unauthorized if the token is missing, invalid, or the user is inactive.
    """

    def authenticate(self, request):
        """
        Authenticate the request using JWT from 'access_token' cookie.
        Raises AuthenticationFailed (401) if token is missing or invalid.

        Args:
            request (HttpRequest): DRF request object.

        Returns:
            tuple: (User instance, token string) if authentication succeeds.

        Raises:
            NotAuthenticated: If token is missing, invalid, or user inactive.
        """
        token = request.COOKIES.get("access_token")

        if not token:
            raise exceptions.NotAuthenticated("Authentication credentials were not provided.")

        try:
            payload = safe_decode(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise exceptions.NotAuthenticated("Token payload missing user_id")

            try:
                user = User.objects.get(user_id=user_id, is_active=True)
            except User.DoesNotExist:
                raise exceptions.NotAuthenticated("User not found or inactive")

            return (user, token)

        except Exception as e:
            logger.warning(f"Invalid access token: {str(e)}")
            raise exceptions.NotAuthenticated("Invalid or expired access token")

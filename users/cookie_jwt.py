from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from users.models import User
import logging
from users.tokens import safe_decode

logger = logging.getLogger(__name__)

class CookieJWTAuthentication(BaseAuthentication):
    """
    Custom DRF authentication class that reads the JWT access token from an HttpOnly cookie.

    Returns None (no authentication) if the token cookie is missing so that permission
    classes can decide (typically resulting in 403 for unauthenticated requests).
    Returns 401 Unauthorized only when a token is present but invalid or the user is inactive.
    """

    def authenticate(self, request):
        """
        Authenticate the request using JWT from 'access_token' cookie.
        Returns None if token is missing.
        Raises AuthenticationFailed (401) if token is present but invalid.

        Args:
            request (HttpRequest): DRF request object.

        Returns:
            tuple: (User instance, token string) if authentication succeeds.

        Raises:
            AuthenticationFailed: If token is invalid or user inactive.
        """
        token = request.COOKIES.get("access_token")

        if not token:
            # No credentials provided; let permission classes handle as unauthenticated (403)
            return None

        try:
            payload = safe_decode(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise exceptions.AuthenticationFailed("Token payload missing user_id")

            try:
                user = User.objects.get(user_id=user_id, is_active=True)
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed("User not found or inactive")

            return (user, token)

        except Exception as e:
            logger.warning(f"Invalid access token: {str(e)}")
            raise exceptions.AuthenticationFailed("Invalid or expired access token")

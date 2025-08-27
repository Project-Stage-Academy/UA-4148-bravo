import logging
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth import get_user_model
from validation.validate_token import safe_decode

logger = logging.getLogger(__name__)
User = get_user_model()


class CookieJWTAuthentication(BaseAuthentication):
    """
    Custom DRF authentication class that reads the JWT access token from an HttpOnly cookie.

    This class looks for a cookie named 'access_token', validates it using `safe_decode`,
    and returns the associated user if the token is valid. It integrates with DRF's
    authentication system, so endpoints protected with `IsAuthenticated` can use this
    mechanism for cookie-based JWT authentication.

    Usage:
        Add this class to `DEFAULT_AUTHENTICATION_CLASSES` in Django REST Framework settings
        or use it on specific views.

    Raises:
        AuthenticationFailed: If the token is missing, invalid, expired, or the user is inactive.
    """

    def authenticate(self, request):
        """
        Authenticate the request using JWT from an HttpOnly cookie.

        Steps:
        1. Retrieve the 'access_token' cookie from the request.
        2. If no cookie is present, return None to let DRF handle it as unauthenticated.
        3. Decode and validate the JWT using `safe_decode`.
        4. Extract `user_id` from the token payload.
        5. Retrieve the corresponding active user from the database.
        6. Return a `(user, token)` tuple if valid; otherwise, raise AuthenticationFailed.

        Args:
            request (HttpRequest): DRF request object.

        Returns:
            tuple: (User instance, token string) if authentication succeeds.
            None: If no token is provided (DRF treats it as unauthenticated).

        Raises:
            AuthenticationFailed: If the token is invalid, expired, or the user does not exist.
        """
        token = request.COOKIES.get("access_token")
        if not token:
            return None

        try:
            payload = safe_decode(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise exceptions.AuthenticationFailed("Token payload missing user_id")

            try:
                user = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                raise exceptions.AuthenticationFailed("User not found or inactive")

            return (user, token)
        except Exception as e:
            logger.warning(f"Invalid access token: {str(e)}")
            raise exceptions.AuthenticationFailed("Invalid or expired access token")

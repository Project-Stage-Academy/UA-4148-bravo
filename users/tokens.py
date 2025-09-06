import logging
import jwt
from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import User

logger = logging.getLogger(__name__)


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for email verification.

    Generates tokens based on:
      - user.pk (primary key)
      - timestamp
      - user.is_active
      - user.email_verification_token field (if present)
      - optionally, user.pending_email if implemented

    Tokens become invalid if:
      - The user is deactivated.
      - The rotation token changes.
      - The pending email changes (if used).
    """

    def _make_hash_value(self, user: User, timestamp: int) -> str:
        """
        Construct a unique hash value for token generation.

        Args:
            user (User): The user instance.
            timestamp (int): Token generation timestamp.

        Returns:
            str: String uniquely identifying the token for the user.
        """
        parts = [
            str(getattr(user, 'pk', '')),
            str(timestamp),
            str(getattr(user, 'is_active', False)),
            str(getattr(user, 'email_verification_token', '')),
        ]

        pending_email = getattr(user, 'pending_email', None)
        if pending_email:
            parts.append(str(pending_email))

        return ":".join(filter(None, parts))


EMAIL_VERIFICATION_TOKEN = EmailVerificationTokenGenerator()


def make_uidb64(user_id: int) -> str:
    """
    Encode user_id to a URL-safe base64 string.

    Args:
        user_id (int): User primary key.

    Returns:
        str: Base64 encoded user ID.
    """
    return urlsafe_base64_encode(force_bytes(str(user_id)))


def safe_decode(token: str):
    """
    Safely decode a JWT and verify its signature and expiration.
    Raises InvalidToken or TokenExpired if the token is invalid or expired.
    """
    if not token or len(token.split(".")) != 3:
        raise InvalidToken("Token is malformed.")

    try:
        payload = jwt.decode(
            token,
            key=settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_exp": True}
        )
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired.")
    except Exception as e:
        raise InvalidToken(f"Could not decode token: {str(e)}")

    return payload


def make_token(user: User) -> str:
    """
    Generate an email verification token for the user.

    Args:
        user (User): User instance.

    Returns:
        str: Token string.
    """
    if user is None:
        raise ValueError("Cannot generate token: user must not be None.")

    if not user.is_active:
        raise ValueError("Cannot generate token: user is inactive.")

    return EMAIL_VERIFICATION_TOKEN.make_token(user)


def check_token(user: User, token: str) -> bool:
    """
    Validate the token for the user.

    Args:
        user (User): User instance.
        token (str): Token string.

    Returns:
        bool: True if valid, False otherwise.
    """
    if user is None:
        raise ValueError("Cannot check token: user must not be None.")
    if not token:
        raise ValueError("Cannot check token: token must not be None.")
    return EMAIL_VERIFICATION_TOKEN.check_token(user, token)

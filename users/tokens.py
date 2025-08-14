import logging
from typing import Optional
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
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


def decode_uidb64(uidb64: str) -> Optional[int]:
    """
    Decode a base64 string back to user_id.

    Args:
        uidb64 (str): Base64 encoded user ID.

    Returns:
        Optional[Union[int, str]]: Decoded user ID as int if possible, else str. None if decoding fails.
    """
    try:
        decoded = force_str(urlsafe_base64_decode(uidb64))
        if decoded.isdigit():
            return int(decoded)
        return decoded 
    except (TypeError, ValueError, OverflowError) as e:
        logger.error(f"Failed to decode uidb64 '{uidb64}': {e}", exc_info=True)
        return None


def make_token(user: User) -> str:
    """
    Generate an email verification token for the user.

    Args:
        user (User): User instance.

    Returns:
        str: Token string.
    """
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
    return EMAIL_VERIFICATION_TOKEN.check_token(user, token)
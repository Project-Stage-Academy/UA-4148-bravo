from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Token generator for email verification.

    Generates tokens based on:
      - user.pk (primary key, universal)
      - timestamp
      - user.is_active
      - user.email_verification_token field (if present, for manual rotation)
      - optionally, user.pending_email if implemented

    This ensures tokens become invalid if:
      - The user is deactivated.
      - The rotation token changes.
      - The pending email changes (if used).
    """

    def _make_hash_value(self, user, timestamp):
        """
        Construct a unique hash value for token generation.

        Args:
            user (User): The user instance.
            timestamp (int): Token generation timestamp.

        Returns:
            str: String uniquely identifying the token for the user.
        """
        base = f"{getattr(user, 'pk', '')}{timestamp}{getattr(user, 'is_active', False)}"

        rotation_token = getattr(user, 'email_verification_token', None)
        if rotation_token:
            base += str(rotation_token)

        pending_email = getattr(user, 'pending_email', None)
        if pending_email:
            base += str(pending_email)

        return base


email_verification_token = EmailVerificationTokenGenerator()


def make_uidb64(user_id):
    """
    Encode user_id to a URL-safe base64 string.

    Args:
        user_id (int): User primary key.

    Returns:
        str: Base64 encoded user ID.
    """
    return urlsafe_base64_encode(force_bytes(user_id))


def decode_uidb64(uidb64):
    """
    Decode a base64 string back to user_id.

    Args:
        uidb64 (str): Base64 encoded user ID.

    Returns:
        int or None: Decoded user ID, or None if decoding fails.
    """
    try:
        return int(force_str(urlsafe_base64_decode(uidb64)))
    except (TypeError, ValueError, OverflowError):
        return None


def make_token(user):
    """
    Generate an email verification token for the user.

    Args:
        user (User): User instance.

    Returns:
        str: Token string.
    """
    return email_verification_token.make_token(user)


def check_token(user, token):
    """
    Validate the token for the user.

    Args:
        user (User): User instance.
        token (str): Token string.

    Returns:
        bool: True if valid, False otherwise.
    """
    return email_verification_token.check_token(user, token)
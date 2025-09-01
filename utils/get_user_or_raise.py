from django.core.exceptions import ValidationError
import logging
import sentry_sdk

logger = logging.getLogger(__name__)


def get_user_or_raise(email, room_name):
    """
    Retrieve a User by email or raise a ValidationError if the user does not exist.

    Args:
        email (str): The email address of the user to retrieve.
        room_name (str): The name of the room, used for logging and error reporting.

    Returns:
        User: The User instance corresponding to the given email.

    Raises:
        ValidationError: If no user with the given email exists.
    """
    try:
        from users.models import User
        return User.objects.get(email=email)
    except User.DoesNotExist:
        msg = f"User does not exist: {email}"
        logger.error("[ROOM_VALIDATION] %s | room=%s", msg, room_name)
        sentry_sdk.capture_message(msg, level="error")
        raise ValidationError(msg)

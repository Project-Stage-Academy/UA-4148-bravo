from django.core.validators import validate_email
from django.core.exceptions import ValidationError


def validate_email_custom(value):
    """
    Validates that the given value is a properly formatted email address.

    This function uses Django's built-in `validate_email` to check the format.
    If the email is invalid, it raises a `ValidationError` with a custom message.

    Args:
        value (str): The email address to validate.

    Raises:
        ValidationError: If the email address format is invalid.
    """
    try:
        validate_email(value)
    except ValidationError:
        raise ValidationError("Invalid email address format.")

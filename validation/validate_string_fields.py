from django.core.exceptions import ValidationError


def validate_max_length(value, max_length, field_name):
    """
    Validates that the value does not exceed the maximum length.

    Args:
        value (str): The string to validate.
        max_length (int): Maximum allowed length.
        field_name (str): Name of the field for error messages.

    Raises:
        ValidationError: If value exceeds max_length.
    """
    if value and len(value) > max_length:
        raise ValidationError(f"{field_name} must be {max_length} characters or fewer")

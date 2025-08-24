import re
from django.core.exceptions import ValidationError

LATIN_REGEX = re.compile(r"^[A-Za-z0-9\s\-']+$")
FORBIDDEN_NAMES = {name.lower() for name in {"other", "none", "misc", "default"}}


def validate_company_name(value):
    """
    Validate company name for startups and investors.

    Args:
        value (str): Company name to validate

    Returns:
        str: Validated and stripped company name

    Raises:
        ValidationError: If company name is invalid
    """
    value = str(value).strip()

    if not value:
        raise ValidationError("Company name must not be empty.")

    return value


def validate_latin(value: str) -> bool:
    """
    Checks whether the text contains only Latin letters,
    spaces, hyphens, or apostrophes.

    Args:
    text (str): The text to check.

    Returns:
    bool: True if the text matches the pattern, False otherwise.
    """
    return bool(LATIN_REGEX.match(value.strip()))


def validate_forbidden_names(name: str, field_name: str = "name"):
    """
    Validates a name string to ensure it:
    - Is not empty or only whitespace.
    - Contains only Latin letters, spaces, hyphens, or apostrophes.
    - Is not a generic or reserved word (e.g., 'other', 'none').

    Args:
        name (str): The name string to validate.
        field_name (str): The name of the field being validated (used in error messages).

    Raises:
        ValidationError: If the name is empty, contains non-Latin characters,
                         or is a forbidden value.
    """
    name = validate_company_name(name)

    if not validate_latin(name):
        raise ValidationError(
            {field_name: "The name must contain only Latin letters, spaces, hyphens, or apostrophes."})

    if name.lower() in FORBIDDEN_NAMES:
        raise ValidationError({
            field_name: "This name is too generic or reserved. Please write a more specific name."
        })

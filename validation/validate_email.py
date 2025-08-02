from django.core.validators import validate_email
from django.core.exceptions import ValidationError

def validate_email_custom(value):
    try:
        validate_email(value)
    except ValidationError:
        raise ValidationError("Invalid email address format.")

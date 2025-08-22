from django.core.exceptions import ValidationError
import re

class CustomPasswordValidator:
    """
    Validate that the password contains at least one uppercase letter,
    one lowercase letter, and one digit.
    """
    def validate(self, password, user=None):
        """
        Validate password complexity requirements.

        Args:
            password (str): The password to validate.
            user (User, optional): The user object. Not used in this validator.

        Raises:
            ValidationError: If the password doesn't meet complexity requirements.
        """
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'\d', password):
            raise ValidationError("Password must contain at least one number.")
    
    def get_help_text(self):
        """
        Return the help text describing password requirements.

        Returns:
            str: A string explaining the password rules.
        """
        return "Password must contain uppercase and lowercase letters and numbers."

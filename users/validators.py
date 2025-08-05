from django.core.exceptions import ValidationError
import re

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contains at least one uppercase letter.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contains at least one lowercase letter.")
        if not re.search(r'\d', password):
            raise ValidationError("Password must contains at least one number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError("Password must contains at least one special symbol.")
    
    def get_help_text(self):
        return "Password must contains uppercase and lowercase letters, numbers and special symbols."

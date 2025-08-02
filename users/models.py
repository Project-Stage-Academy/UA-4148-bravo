from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxLengthValidator
from django.db import models
from validation.validate_email import validate_email_custom


class CustomUser(AbstractUser):
    email = models.EmailField(
        max_length=255,
        validators=[validate_email_custom],
        unique=True
    )
    user_phone = models.CharField(
        max_length=20,
        validators=[MaxLengthValidator(20)]
    )
    title = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=[
            ('active', 'Active'),
            ('pending', 'Pending'),
            ('blocked', 'Blocked'),
            ('deleted', 'Deleted'),
        ],
        default='active',
        validators=[MaxLengthValidator(10)]
    )

    def __str__(self):
        return f"{self.username} ({self.email}) - {self.status}"

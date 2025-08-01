from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Project(models.Model):
    startup_profile = models.ForeignKey(
        'StartUpProfile',
        on_delete=models.CASCADE,
        related_name='projects'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    funding_goal = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    current_funding = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    funding_progress_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ]
    )

    category = models.CharField(max_length=100, blank=True, null=True)
    banner_image_url = models.URLField(blank=True, null=True)

    has_patents = models.BooleanField(default=False)
    is_participant = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} — {self.startup_profile.company_name}"

    def save(self, *args, **kwargs):
        # Automatically calculate funding progress
        if self.funding_goal and self.funding_goal > 0:
            self.funding_progress_percent = min(
                (self.current_funding / self.funding_goal) * 100, 100
            )
        else:
            self.funding_progress_percent = 0
        super().save(*args, **kwargs)

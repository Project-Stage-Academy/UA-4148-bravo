from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from validation.validate_email import validate_email_custom


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    startup = models.ForeignKey('profiles.Startup', on_delete=models.CASCADE, related_name='projects')
    investor = models.ForeignKey('profiles.Investor', on_delete=models.CASCADE, related_name='projects')

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    business_plan = models.FileField(upload_to='projects/business_plans/', blank=True, null=True)
    media_files = models.FileField(upload_to='projects/media/', blank=True, null=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    duration = models.PositiveIntegerField(
        help_text="Duration in days",
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(3650)  # до 10 років
        ]
    )

    funding_goal = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.01'))
        ]
    )
    current_funding = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00'))
        ]
    )

    category = models.ForeignKey('Category', on_delete=models.PROTECT)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(
        max_length=255,
        validators=[validate_email_custom],
        unique=True
    )

    has_patents = models.BooleanField(default=False)
    is_participant = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Project '{self.title}' by {self.startup}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

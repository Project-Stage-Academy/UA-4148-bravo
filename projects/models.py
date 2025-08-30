from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from validation.validate_document import validate_document_file
from validation.validate_email import validate_email_custom
from validation.validate_names import validate_forbidden_names

from common.enums import ProjectStatus


class Category(models.Model):
    """
    Represents a category for projects or other entities.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        validate_forbidden_names(self.name, field_name="name")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        db_table = 'categories'


class Project(models.Model):
    """
    Represents a startup project with details about funding, status, and documentation.
    """

    startup = models.ForeignKey(
        'startups.Startup',
        on_delete=models.CASCADE,
        related_name='projects'
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")

    business_plan = models.FileField(
        upload_to='projects/business_plans/',
        blank=True,
        null=True,
        validators=[validate_document_file]
    )

    media_files = models.FileField(
        upload_to='projects/media/',
        blank=True,
        null=True,
        validators=[validate_document_file]
    )

    status = models.CharField(
        max_length=50,
        choices=ProjectStatus.choices,
        default=ProjectStatus.DRAFT
    )

    duration = models.PositiveIntegerField(
        help_text="Duration in days",
        blank=True,
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(3650)]
    )

    funding_goal = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    current_funding = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    category = models.ForeignKey('Category', on_delete=models.PROTECT)
    website = models.URLField(blank=True, default="")
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

    technologies_used = models.CharField(max_length=255, blank=True, default="", help_text="Technologies used in the project, comma-separated")
    milestones = models.JSONField(default=dict, blank=True, help_text="Project milestones or roadmap")


    def clean(self):
        """
        Validates the Project instance.

        - Current funding must not exceed the funding goal.
        - Business plan is required if the project is in progress or completed.
        - Funding goal is required if the project is marked as a participant.

        Raises:
            ValidationError: A dictionary of field-specific error messages.
        """
        errors = {}

        if self.funding_goal is not None and self.current_funding > self.funding_goal:
            errors['current_funding'] = 'Current funding cannot exceed funding goal.'

        if self.status in [ProjectStatus.IN_PROGRESS, ProjectStatus.COMPLETED] and not self.business_plan:
            errors['business_plan'] = 'Business plan is required for projects in progress or completed.'

        if self.is_participant and not self.funding_goal:
            errors['funding_goal'] = 'Funding goal is required for participant projects.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Project '{self.title}' by {self.startup}"

    class Meta:
        db_table = 'projects'
        ordering = ['-created_at']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        indexes = [
            models.Index(fields=['status'], name='project_status_idx'),
            models.Index(fields=['created_at'], name='project_created_at_idx'),
            models.Index(fields=['startup'], name='project_startup_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['title', 'startup'], name='unique_startup_project_title')
        ]
class ProjectHistory(models.Model):
    """
    Stores a history of changes for the Project model.
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_fields = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "project_history"
        ordering = ['-timestamp']
        verbose_name = "Project History"
        verbose_name_plural = "Project Histories"

    def __str__(self):
        return f"History for {self.project.title} at {self.timestamp}"
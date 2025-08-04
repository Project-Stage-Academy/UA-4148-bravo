import re
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from validation.validate_document import validate_document_file
from validation.validate_email import validate_email_custom
from django.core.exceptions import ValidationError


class Category(models.Model):
    """
    Represents a category for projects or other entities.

    Validation:
    - Name must contain only Latin characters.
    - Name cannot be a generic or reserved term like 'other', 'none', 'misc', or 'default'.

    Fields:
    - name: Unique name of the category.
    - description: Optional detailed description.
    - created_at: Timestamp of creation.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        '''
        Disallow non-Latin letters (allow any characters as long as letters are Latin)
        Disallow vague or reserved category names
        '''
        super().clean()

        if re.search(r'[^\x00-\x7F]', self.name):
            raise ValidationError({
                'name': "The name must contain only Latin characters. "
                        "Non-Latin characters are not allowed."
            })

        forbidden_names = {"other", "none", "misc", "default"}
        if self.name.strip().lower() in forbidden_names:
            raise ValidationError({
                'name': "This name is too generic or reserved. "
                        "Please write a more specific category name."
            })

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

    Validation:
    - Current funding must not exceed the funding goal.
    - Business plan is required if the project is in progress or completed.
    - Funding goal is required if the project is marked as a participant.

    Fields:
    - startup: ForeignKey to the Startup that owns the project.
    - title: Title of the project.
    - description: Optional project description.
    - business_plan: Optional uploaded business plan document.
    - media_files: Optional uploaded media files related to the project.
    - status: Project status with choices (draft, in progress, completed, cancelled).
    - duration: Duration of the project in days.
    - funding_goal: Target funding amount (optional).
    - current_funding: Current amount of funding received.
    - category: Category of the project.
    - website: Project website URL (optional).
    - email: Contact email for the project, must be unique.
    - has_patents: Whether the project has patents.
    - is_participant: Whether the project is a participant (e.g. in a program).
    - is_active: Whether the project is active.
    - created_at: Timestamp of creation.
    - updated_at: Timestamp of last update.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    startup = models.ForeignKey(
        'profiles.Startup',
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
        choices=STATUS_CHOICES,
        default='draft'
    )
    duration = models.PositiveIntegerField(
        help_text="Duration in days",
        blank=True,
        default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(3650)
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

    def clean(self):
        """
        Perform custom validation for the Project model.

        Validates the following:
        - Current funding must not exceed the funding goal.
        - Business plan is required if the project is in progress or completed.
        - Funding goal is required if the project is marked as a participant.
        """
        errors = {}

        if self.funding_goal is not None and self.current_funding > self.funding_goal:
            errors['current_funding'] = 'Current funding cannot exceed funding goal.'

        if self.status in ['in_progress', 'completed'] and not self.business_plan:
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

import datetime

from django.core.exceptions import ValidationError
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator
)
from django.db import models

from validation.validate_email import validate_email_custom
from validation.validate_image import validate_image_file


class Stage(models.TextChoices):
    """
    Enumeration of possible stages for companies (startups and investors).
    Stages represent the lifecycle or maturity of a company, such as idea, prototype,
    MVP, growth, scale, and enterprise.
    """
    IDEA = 'idea', 'Idea'
    PROTOTYPE = 'prototype', 'Prototype'
    MVP = 'mvp', 'MVP'
    GROWTH = 'growth', 'Growth'
    SCALE = 'scale', 'Scale'
    ENTERPRISE = 'enterprise', 'Enterprise'

    @classmethod
    def display(cls, value: str) -> str:
        """
        Returns the human-readable label for a given stage value.

        Example:
            Stage.display("mvp") -> "MVP"
        """
        try:
            return cls(value).label
        except ValueError:
            return value


class Company(models.Model):
    """
    Abstract base model representing common attributes of companies such as
    startups and investors.

    Fields:
    - user: One-to-one link to the associated user account.
    - industry: Industry category of the company.
    - company_name: Official name of the company.
    - location: Geographic location of the company.
    - logo: Image file for the company's logo, validated for file type and size.
    - description: Optional textual description of the company.
    - website: Company's website URL.
    - email: Contact email address (must be unique).
    - founded_year: Year the company was founded, constrained between 1900 and current year.
    - team_size: Number of employees or team members, minimum of 1.
    - stage: Current stage of the company lifecycle, optional but set by default
      depending on whether it is a startup or investor.
    - created_at: Timestamp when the record was created.
    - updated_at: Timestamp when the record was last updated.

    Validation:
    - Website must begin with 'http://' or 'https://'.
    - Founded year cannot be in the future.
    - Team size must be at least 1.
    - Description must be at least 10 characters if provided.
    - Default stage is assigned during validation if not set, based on subclass type.

    This class is abstract and intended to be subclassed.
    """
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE
    )
    industry = models.ForeignKey(
        'profiles.Industry',
        on_delete=models.PROTECT
    )
    company_name = models.CharField(max_length=254, unique=True)
    location = models.ForeignKey(
        'profiles.Location',
        on_delete=models.PROTECT
    )
    logo = models.ImageField(
        upload_to='company/logos/',
        validators=[validate_image_file],
        blank=True,
        null=True
    )
    description = models.TextField(blank=True, default="")
    website = models.URLField(blank=True, default="")
    email = models.EmailField(
        max_length=254,
        validators=[validate_email_custom],
        unique=True
    )
    founded_year = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(datetime.datetime.now().year)
        ]
    )
    team_size = models.PositiveIntegerField(
        blank=True,
        default=1,
        validators=[MinValueValidator(1)]
    )
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """ Description must be at least 10 characters if provided. """
        if self.description:
            trimmed_description = self.description.strip()
            if len(trimmed_description) < 10:
                raise ValidationError({
                    'description': "Description must be at least 10 characters long if provided."
                })

    class Meta:
        abstract = True
        ordering = ['company_name']

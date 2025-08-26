import datetime

from django.core.exceptions import ValidationError
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator
)
from django.db import models

from typing import cast
from core import settings

from common.enums import Stage
from validation.validate_email import validate_email_custom
from validation.validate_image import validate_image_file
from validation.validate_names import validate_company_name, validate_latin
from validation.validate_social_links import validate_social_links_dict


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
        'startups.Industry',
        on_delete=models.PROTECT
    )
    company_name = models.CharField(
        max_length=254,
        validators=[validate_company_name, validate_latin],
        unique=True
    )
    location = models.ForeignKey(
        'startups.Location',
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
    social_links = models.JSONField(
        blank=True,
        default=dict,
        verbose_name="Social Links",
        help_text="Social media links as a JSON object"
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
            
        social_links = cast(dict, self.social_links)
        validate_social_links_dict(
            social_links=social_links,
            allowed_platforms=settings.ALLOWED_SOCIAL_PLATFORMS,
            raise_serializer=False
        )
    class Meta:
        abstract = True
        ordering = ['company_name']

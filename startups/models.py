from django.core.exceptions import ValidationError
from django.db import models
from django_countries.fields import CountryField
from typing import cast
from common.company import Company
from common.enums import Stage
from core import settings
from validation.validate_names import validate_forbidden_names, validate_latin
from validation.validate_social_links import validate_social_links_dict


class Location(models.Model):
    """
    Represents a physical location associated with a startup.
    Includes country, region, city, address line, and postal code.
    Validates formatting and logical consistency.
    """
    country = CountryField(
        verbose_name="Country",
        help_text="Country of the location"
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Region",
        help_text="Region or state of the location"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="City",
        help_text="City of the location"
    )
    address_line = models.CharField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name="Address Line",
        help_text="Street address or detailed address line"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Postal Code",
        help_text="Postal or ZIP code"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def clean(self):
        """
        Validates the Location instance:
        - Postal code must be at least 3 characters and contain only Latin letters, spaces, hyphens, or apostrophes.
        - City, region, and address line must not be empty or contain only spaces and must be Latin characters only.
        - Enforces logical dependencies: address_line requires city and region, city requires region.
        """
        errors = {}

        if self.postal_code:
            postal = self.postal_code.strip()
            if len(postal) < 3:
                errors['postal_code'] = "Postal code must be at least 3 characters."
            elif not validate_latin(postal):
                errors['postal_code'] = (
                    "Postal code must contain only Latin letters, spaces, hyphens, or apostrophes."
                )

        for field_name in ['city', 'region', 'address_line']:
            raw_value = getattr(self, field_name)
            if raw_value:
                value = raw_value.strip()
                if not value:
                    errors[field_name] = (
                        f"{field_name.replace('_', ' ').capitalize()} must not be empty or just spaces."
                    )
                elif not validate_latin(value):
                    errors[field_name] = (
                        f"{field_name.replace('_', ' ').capitalize()} must contain only Latin letters, spaces, hyphens, or apostrophes."
                    )

        if self.address_line:
            if not self.city or not self.city.strip():
                errors['city'] = "City is required when address_line is provided."
            if not self.region or not self.region.strip():
                errors['region'] = "Region is required when address_line is provided."

        if self.city:
            if not self.region or not self.region.strip():
                errors['region'] = "Region is required when city is provided."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        values = [
            self.address_line,
            self.city,
            self.region,
            str(self.country) if self.country else None
        ]
        return ", ".join(s for s in values if s)

    class Meta:
        db_table = "locations"
        ordering = ["country"]
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        indexes = [
            models.Index(fields=['country']),
            models.Index(fields=['city']),
            models.Index(fields=['region']),
        ]


class Industry(models.Model):
    """
    Represents an industry category, which can be linked to other entities like startups.
    Enforces uniqueness of the industry name and validates against forbidden names.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Industry Name",
        help_text="Name of the industry (unique)"
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="Description",
        help_text="Optional detailed description of the industry"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def clean(self):
        """
        Validates the Industry name to ensure it does not contain forbidden terms.

        Raises:
            ValidationError: If forbidden names are detected.
        """
        super().clean()
        validate_forbidden_names(self.name, field_name="name")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "industries"
        ordering = ["name"]
        verbose_name = "Industry"
        verbose_name_plural = "Industries"
        indexes = [
            models.Index(fields=['name']),
        ]


class Startup(Company):
    """
    Represents a startup company linked to a user.
    Includes stage of development and social links validation.
    """
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='startup',
        verbose_name="User",
        help_text="User who owns this startup"
    )
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        default=Stage.IDEA,
        verbose_name="Development Stage",
        help_text="Current development stage of the startup"
    )
    social_links = models.JSONField(
        blank=True,
        default=dict,
        verbose_name="Social Links",
        help_text="Social media links as a JSON object"
    )
    industry = models.ForeignKey(
        Industry,
        on_delete=models.SET_NULL,
        null=True,
        related_name='startups'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        related_name='startups'
    )
    founded_year = models.PositiveIntegerField(blank=True, null=True)
    team_size = models.PositiveIntegerField(blank=True, null=True)
    funding_stage = models.CharField(
        max_length=50,
        choices=[
            ('pre_seed', 'Pre-Seed'),
            ('seed', 'Seed'),
            ('series_a', 'Series A'),
            ('series_b', 'Series B'),
            ('growth', 'Growth'),
        ],
        blank=True,
        null=True
    )
    investment_needs = models.TextField(blank=True, null=True)
    company_size = models.CharField(
        max_length=50,
        choices=[
            ('1-10', '1-10'),
            ('11-50', '11-50'),
            ('51-200', '51-200'),
            ('201-500', '201-500'),
            ('500+', '500+'),
        ],
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)

    def clean(self):
        """
        Validates the Startup instance:
        - Ensures social_links only contain allowed platforms.
        - Validates URLs for the platforms.
        """
        super().clean()
        social_links = cast(dict, self.social_links)
        validate_social_links_dict(
            social_links=social_links,
            allowed_platforms=settings.ALLOWED_SOCIAL_PLATFORMS,
            raise_serializer=False
        )

    def __str__(self):
        return self.company_name

    class Meta:
        db_table = "startups"
        ordering = ["company_name"]
        verbose_name = "Startup"
        verbose_name_plural = "Startups"
        indexes = [
            models.Index(fields=['company_name']),
            models.Index(fields=['stage']),
        ]

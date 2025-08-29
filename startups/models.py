from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint, F
from django_countries.fields import CountryField

from common.company import Company
from common.enums import Stage
from validation.validate_names import validate_forbidden_names, validate_latin


class Location(models.Model):
    """
    Represents a physical location with country, region, city, address line, and postal code.
    Includes validation to ensure fields follow expected formats and logical consistency.
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
        Validates the Location instance.

        - Postal code must be at least 3 characters and contain only Latin characters.
        - City, region, and address line must not be empty or contain only spaces and must be Latin characters only.
        - Enforces logical dependencies: address_line requires city and region, city requires region.

        Raises:
            ValidationError: If any validation rules fail.
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
        city_str = self.city if self.city else 'Unknown City'
        country_str = self.country if self.country else 'Unknown Country'

        if self.region:
            return f"{city_str}, {self.region}, {country_str}"
        return f"{city_str}, {country_str}"

    class Meta:
        db_table = "locations"
        ordering = ["country"]
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        constraints = [
            UniqueConstraint(
                F('city'),
                F('region'),
                F('country'),
                name='unique_location',
                violation_error_message='This location already exists.'
            )
        ]
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

    def clean(self):
        """
        Validates the Startup instance.

        - Ensures social_links only contain allowed platforms.
        - Validates URLs for the platforms.

        Raises:
            ValidationError: If social_links are invalid.
        """
        super().clean()

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

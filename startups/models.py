from django.core.exceptions import ValidationError
from django.db import models
from django_countries.fields import CountryField
from django.db.models import UniqueConstraint, F

from common.company import Company
from common.enums import Stage
from core import settings
from validation.validate_names import validate_forbidden_names, validate_latin
from validation.validate_social_links import validate_social_links_dict


class Location(models.Model):
    country = CountryField()
    region = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    address_line = models.CharField(max_length=254, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Validates the Location instance.

        - Ensures postal code is at least 3 characters and contains only Latin characters.
        - Validates city, region, and address_line for non-empty and Latin-only content.
        - Enforces logical dependencies between address_line, city, and region.

        Raises:
            ValidationError: A dictionary of field-specific error messages.
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

        if self.state:
            return f"{city_str}, {self.state}, {country_str}"
        return f"{city_str}, {country_str}"

    class Meta:
        db_table = "locations"
        ordering = ["country"]
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        constraints = [
            UniqueConstraint(
                F('city'),
                F('state'),
                F('country'),
                name='unique_location',
                violation_error_message='This location already exists.'
            )
        ]


class Industry(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """
        Validates the Industry name against forbidden terms.

        Raises:
            ValidationError: If the name contains forbidden content.
        """
        super().clean()
        validate_forbidden_names(self.name, field_name="name")

    def __str__(self):
        return self.name

class Startup(models.Model):
    company_name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, related_name='startups')
    industries = models.ManyToManyField(Industry, related_name='startups')
    funding_stage = models.CharField(max_length=50)

    def __str__(self):
        return self.company_name

    class Meta:
        db_table = "startups"
        ordering = ["company_name"]
        verbose_name = "Startup"
        verbose_name_plural = "Startups"
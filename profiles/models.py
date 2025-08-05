from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django_countries.fields import CountryField

from common.company import Company, Stage
from validation.validate_names import validate_forbidden_names, validate_latin


class Location(models.Model):
    """
    Model representing a geographical location.

    Fields:
    - country: Country of the location, using a specialized CountryField.
    - region: Optional region/state within the country.
    - city: Optional city name.
    - address_line: Optional detailed address line.
    - postal_code: Optional postal or ZIP code.
    - created_at: Timestamp when the record was created.
    - updated_at: Timestamp when the record was last updated.

    Validation rules ensure consistency among fields:
    - If address_line is given, city and region must be provided.
    - If city or region is provided, country must be set.
    - City and region names must contain only alphabetic characters and spaces.
    - Postal code must be at least 3 characters if given.
    """
    country = CountryField()
    region = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    address_line = models.CharField(max_length=254, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Perform validation for the Location model.

        Validates both:
        - Field-level rules:
            - All text fields must contain only Latin characters (if provided).
            - Postal code must be at least 3 characters (if provided).
        - Cross-field rules:
            - If address_line is provided, city and region are required.
            - If city or region is provided, country is required.
            - If city is provided, region is required.

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


class Industry(models.Model):
    """
    Model representing an industry category for companies.

    Fields:
    - name: Unique name of the industry (Latin characters only).
    - description: Optional textual description.
    - created_at: Timestamp of record creation.

    Validation rules:
    - Name must be non-empty and contain only Latin characters.
    - Certain generic or reserved names are disallowed.

    Used for categorizing companies by their field of business.
    """
    name = models.CharField(
        max_length=100,
        unique=True
    )
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """
        Validates the Industry instance before saving.
        Ensures the name is in Latin characters only, not reserved,
        and not too generic. Strips spaces.
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


class Startup(Company):
    """
    Model representing a Startup company.
    Inherits from the base Company model and adds specific fields:
        - stage: The stage of the startup.
        - social_links: A JSON field storing URLs to social media profiles, keyed by platform.
    Includes custom validation logic to ensure social media links are valid.
    String representation includes company name and associated user ID.
    Meta options specify database table, ordering, and verbose names.
    """
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='startup'
    )
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        default=Stage.IDEA
    )
    social_links = models.JSONField(blank=True, default=dict)

    ALLOWED_SOCIAL_PLATFORMS = {
        'facebook': ['facebook.com'],
        'twitter': ['twitter.com'],
        'linkedin': ['linkedin.com'],
        'instagram': ['instagram.com'],
        'youtube': ['youtube.com', 'youtu.be'],
        'tiktok': ['tiktok.com'],
        'telegram': ['t.me', 'telegram.me'],
    }

    def clean(self):
        """
        Validates and prepares the Startup instance before saving.

        Responsibilities:
        - Sets a default value for `stage` if not explicitly provided.
        - Calls base model's clean() to perform shared validation.
        - Validates the `social_links` dictionary:
            - Ensures each platform is among the supported platforms.
            - Ensures each URL domain corresponds to the expected domain(s) for that platform.
        Raises:
            ValidationError: If the `social_links` contain unsupported platforms or mismatched domains.
        """
        if not self.stage:
            self.stage = Stage.IDEA
        super().clean()
        errors = {}
        for platform, url in self.social_links.items():
            platform_lc = platform.lower()
            if platform_lc not in self.ALLOWED_SOCIAL_PLATFORMS:
                errors[platform] = f"Platform '{platform}' is not supported."
                continue

            domain = urlparse(url).netloc.lower()
            if not any(allowed in domain for allowed in self.ALLOWED_SOCIAL_PLATFORMS[platform_lc]):
                errors[platform] = f"Invalid URL for platform '{platform}': {url}"

        if errors:
            raise ValidationError({'social_links': errors})

    def __str__(self):
        return f"{self.company_name} (Startup, User ID: {self.user_id})"

    class Meta:
        db_table = "startups"
        ordering = ["company_name"]
        verbose_name = "Startup"
        verbose_name_plural = "Startups"


class Investor(Company):
    """
    Model representing an investor company.
    Extends the base Company model with:
        - stage: The preferred stage of the investor.
        - fund_size: Decimal field representing the size of the investment fund.
    String representation includes company name and associated user ID.
    Meta options specify database table, ordering, and verbose names.
    """
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='investor'
    )
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        default=Stage.MVP
    )
    fund_size = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        default=0,
        validators=[MinValueValidator(0)]
    )

    def clean(self):
        """
        Validates and prepares the Investor instance before saving.
        Responsibilities:
        - Sets a default value for `stage` if not explicitly provided.
        - Calls base model's clean() to perform shared validation.
        """
        if not self.stage:
            self.stage = Stage.MVP
        super().clean()

    def __str__(self):
        return f"{self.company_name} (Investor, User ID: {self.user_id})"

    class Meta:
        db_table = "investors"
        ordering = ["company_name"]
        verbose_name = "Investor"
        verbose_name_plural = "Investors"
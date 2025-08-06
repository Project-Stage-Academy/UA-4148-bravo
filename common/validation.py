from urllib.parse import urlparse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from profiles.models import Startup  # Used to access allowed social platforms


class SocialLinksValidationMixin:
    """
    Shared validation logic for social_links field.
    Ensures platforms are supported, URLs are well-formed, and domains match expected values.
    """
    def validate_social_links(self, value):
        allowed_domains = Startup.ALLOWED_SOCIAL_PLATFORMS
        url_validator = URLValidator()
        errors = {}

        for platform, url in value.items():
            platform_lc = platform.lower()

            # Check if platform is supported
            if platform_lc not in allowed_domains:
                errors[platform] = f"Platform '{platform}' is not supported."
                continue

            # Validate URL format
            try:
                url_validator(url)
            except DjangoValidationError:
                errors[platform] = f"Malformed URL for platform '{platform}': {url}"
                continue

            # Validate domain
            domain = urlparse(url).netloc.lower()
            domain_list = allowed_domains.get(platform_lc, [])

            # Ensure domain_list is iterable
            if isinstance(domain_list, str):
                domain_list = [domain_list]
            elif not isinstance(domain_list, (list, tuple, set)):
                domain_list = []

            if not any(allowed in domain for allowed in domain_list):
                errors[platform] = f"Invalid domain for platform '{platform}': {url}"

        if errors:
            raise serializers.ValidationError({'social_links': errors})

        return value

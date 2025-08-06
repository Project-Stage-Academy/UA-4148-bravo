from urllib.parse import urlparse
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
from rest_framework import serializers


class SocialLinksValidationMixin:
    """
    Provides validation logic for the `social_links` field.

    This method ensures that:
    - Each platform key is supported (based on settings.ALLOWED_SOCIAL_PLATFORMS).
    - Each URL is syntactically valid.
    - The domain of each URL matches one of the expected domains for the given platform.

    Args:
        value (dict): A dictionary of platform names mapped to URLs.

    Returns:
        dict: The validated `social_links` dictionary.

    Raises:
        serializers.ValidationError: If any platform is unsupported, any URL is malformed,
                                     or any domain does not match the expected values.
    """
    def validate_social_links(self, value):
        allowed_domains = settings.ALLOWED_SOCIAL_PLATFORMS
        url_validator = URLValidator()
        errors = {}

        for platform, url in value.items():
            platform_lc = platform.lower()

            if platform_lc not in allowed_domains:
                errors[platform] = f"Platform '{platform}' is not supported."
                continue

            try:
                url_validator(url)
            except DjangoValidationError:
                errors[platform] = f"Malformed URL for platform '{platform}': {url}"
                continue

            domain = urlparse(url).netloc.lower()
            domain_list = allowed_domains.get(platform_lc, [])

            if isinstance(domain_list, str):
                domain_list = [domain_list]
            elif not isinstance(domain_list, (list, tuple, set)):
                domain_list = []

            if not any(allowed in domain for allowed in domain_list):
                errors[platform] = f"Invalid domain for platform '{platform}': {url}"

        if errors:
            raise serializers.ValidationError({'social_links': errors})

        return value
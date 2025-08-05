from urllib.parse import urlparse
from rest_framework import serializers
from profiles.models import Startup  # Used to access allowed social platforms


class SocialLinksValidationMixin:
    """
    Shared validation logic for social_links field.
    Ensures platforms are supported and URLs match expected domains.
    """
    def validate_social_links(self, value):
        allowed_domains = Startup.ALLOWED_SOCIAL_PLATFORMS
        errors = {}

        for platform, url in value.items():
            platform_lc = platform.lower()
            if platform_lc not in allowed_domains:
                errors[platform] = f"Platform '{platform}' is not supported."
                continue

            domain = urlparse(url).netloc.lower()
            if not any(allowed in domain for allowed in allowed_domains[platform_lc]):
                errors[platform] = f"Invalid URL for platform '{platform}': {url}"

        if errors:
            raise serializers.ValidationError({'social_links': errors})

        return value

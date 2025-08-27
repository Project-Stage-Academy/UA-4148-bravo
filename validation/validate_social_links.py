from urllib.parse import urlparse
from django.core.validators import URLValidator
from publicsuffix2 import get_sld


def validate_social_links_dict(social_links, allowed_platforms, raise_serializer=False):
    """
    Validates a dictionary of social links.

    Args:
        social_links (dict): The dict to validate.
        allowed_platforms (dict): Platform -> list of allowed base domains (e.g., 'linkedin.com').
        raise_serializer (bool): Whether to raise DRF ValidationError (True) or Django's (False).

    Raises:
        ValidationError: Either DRF or Django, depending on raise_serializer.
    """
    from rest_framework.exceptions import ValidationError as DRFValidationError
    from django.core.exceptions import ValidationError as DjangoValidationError

    url_validator = URLValidator()
    errors = {}

    for platform, url in social_links.items():
        platform_lc = platform.lower()

        if platform_lc not in allowed_platforms:
            errors[platform] = f"Platform '{platform}' is not supported."
            continue

        try:
            url_validator(url)
        except DjangoValidationError:
            errors[platform] = f"Malformed URL for platform '{platform}': {url}"
            continue

        parsed_url = urlparse(url)
        netloc = parsed_url.netloc.lower()

        try:
            sld = get_sld(netloc)
        except ValueError:
            errors[platform] = f"Could not parse domain for platform '{platform}': {netloc}"
            continue

        allowed_domains = allowed_platforms.get(platform_lc, [])
        if isinstance(allowed_domains, str):
            allowed_domains = [allowed_domains]
        elif not isinstance(allowed_domains, (list, tuple, set)):
            allowed_domains = []

        if sld not in allowed_domains:
            errors[platform] = f"Invalid domain for platform '{platform}': {netloc}"

    if errors:
        raise (DRFValidationError if raise_serializer else DjangoValidationError)(errors)

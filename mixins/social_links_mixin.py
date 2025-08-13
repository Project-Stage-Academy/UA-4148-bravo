from core import settings
from validation.validate_social_links import validate_social_links_dict


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
        validate_social_links_dict(
            social_links=value,
            allowed_platforms=settings.ALLOWED_SOCIAL_PLATFORMS,
            raise_serializer=True
        )
        return value

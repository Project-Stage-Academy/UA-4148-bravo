import bleach
from core.settings.constants import ALLOWED_TAGS, ALLOWED_ATTRIBUTES


def sanitize_message(text: str) -> str:
    """
    Sanitize chat message text against XSS using bleach.

    Args:
        text (str): Raw user input.

    Returns:
        str: Cleaned and safe text.
    """
    return bleach.clean(
        text.strip(),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )

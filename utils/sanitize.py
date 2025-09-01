import html
import re

import bleach
from django.core.exceptions import ValidationError

from core.settings.constants import ALLOWED_TAGS, ALLOWED_ATTRIBUTES


def sanitize_message(text: str) -> str:
    """
    Sanitize chat message text against XSS using bleach.

    Args:
        text (str): Raw user input.

    Returns:
        str: Cleaned and safe text.
    """
    clean_text = bleach.clean(
        text.strip(),
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    if not clean_text:
        raise ValidationError("Message text cannot be empty after sanitization.")
    return clean_text


def sanitize_room_name(name: str) -> str:
    clean_name = bleach.clean(name.strip(), tags=[], attributes={}, strip=True)

    if not clean_name:
        clean_name = re.sub(r"[<>]", "", name.strip())

    clean_name = html.unescape(clean_name)

    if not clean_name or len(clean_name) < 3:
        raise ValidationError("Room name is invalid after sanitization.")

    return clean_name

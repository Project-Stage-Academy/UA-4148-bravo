import filetype
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_document_file(file):
    """
    Validates an uploaded document file:
    - Checks if the file extension is in the allowed list from settings.
    - Ensures file size does not exceed the limit from settings.
    - Uses `filetype` to detect MIME type and validates it against allowed MIME types from settings.

    Args:
        file (File): The uploaded file to validate.

    Raises:
        ValidationError: If the file is invalid due to extension, size, or MIME type.
    """
    if not file:
        raise ValidationError("No file was uploaded.")

    ext = file.name.rsplit('.', 1)[-1].lower()
    if ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file extension: .{ext}. Allowed: {', '.join(settings.ALLOWED_DOCUMENT_EXTENSIONS)}"
        )

    if file.size > settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"The file size must not exceed {settings.MAX_DOCUMENT_SIZE_MB}MB.")

    # Detect MIME type
    file.seek(0)
    kind = filetype.guess(file.read(262))  # Read enough bytes for detection

    if kind is None:
        raise ValidationError("Unable to detect the file type. The file may be corrupted or unsupported.")

    mime_type = kind.mime
    if mime_type not in settings.ALLOWED_DOCUMENT_MIME_TYPES:
        raise ValidationError(f"Invalid MIME type: {mime_type}. This file type is not allowed.")

    file.seek(0)  # Reset pointer for future reads

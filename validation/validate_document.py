import magic
from django.core.exceptions import ValidationError


def validate_document_file(file):
    """
    Validates an uploaded document file for:
    - Allowed file extensions
    - Allowed MIME types
    - Maximum file size (20MB)

    Args:
        file (File): The uploaded file to validate.

    Raises:
        ValidationError: If the file is invalid based on extension, MIME type, or size.
    """

    allowed_extensions = [
        "pdf", "doc", "docx", "txt", "odt", "rtf",
        "xls", "xlsx", "ppt", "pptx", "zip", "rar"
    ]
    ext = file.name.split('.')[-1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"Unsupported file extension: .{ext}. Allowed: {', '.join(allowed_extensions)}")

    max_size_mb = 20
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"The file size must not exceed {max_size_mb}MB.")

    file.seek(0)
    mime_type = magic.from_buffer(file.read(2048), mime=True)

    allowed_mime_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/vnd.oasis.opendocument.text",
        "application/rtf",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
        "application/x-rar-compressed",
    ]

    if mime_type not in allowed_mime_types:
        raise ValidationError(f"Invalid MIME type: {mime_type}. This file type is not allowed.")

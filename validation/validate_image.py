from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from PIL import Image

file_extension_validator = FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png"])


def validate_image_file(file):
    """
    Validate an uploaded image file:
    - Checks extension using FileExtensionValidator.
    - Checks that file is not empty.
    - Checks file size does not exceed 10MB.
    - Validates that the file is a valid image.
    - Validates image dimensions (max 5000x5000).
    - Validates image mode (RGB or RGBA).
    """
    if not file:
        raise ValidationError("No file was uploaded.")

    file_extension_validator(file)

    max_size_mb = 10
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"The file size must not exceed {max_size_mb}MB.")

    try:
        image = Image.open(file)
        image.verify()
    except Exception:
        raise ValidationError("The uploaded file is not a valid image.")

    file.seek(0)
    image = Image.open(file)

    max_width, max_height = 5000, 5000
    if image.width > max_width or image.height > max_height:
        raise ValidationError(f"Image dimensions must not exceed {max_width}x{max_height}px.")

    if image.mode not in ["RGB", "RGBA"]:
        raise ValidationError("Unsupported image mode. Only RGB and RGBA are allowed.")

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from PIL import Image, UnidentifiedImageError
from django.conf import settings

file_extension_validator = FileExtensionValidator(
    allowed_extensions=settings.ALLOWED_IMAGE_EXTENSIONS
)


def validate_image_file(file):
    """
    Validates an uploaded image file:
    - Validates file extension using FileExtensionValidator.
    - Checks size limit.
    - Verifies it's a valid image using Pillow.
    - Validates image dimensions and mode.

    Raises:
        ValidationError: If the image is invalid based on any criteria.
    """
    if not file:
        raise ValidationError("No file was uploaded.")

    file_extension_validator(file)

    if file.size > settings.MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"The file size must not exceed {settings.MAX_IMAGE_SIZE_MB}MB.")

    try:
        image = Image.open(file)
        image.verify()
    except UnidentifiedImageError:
        raise ValidationError("The uploaded file is not a valid image.")
    except Exception:
        raise ValidationError("Failed to process the image. It may be corrupted or unsupported.")

    file.seek(0)
    image = Image.open(file)

    max_width, max_height = settings.MAX_IMAGE_DIMENSIONS
    if image.width > max_width or image.height > max_height:
        raise ValidationError(f"Image dimensions must not exceed {max_width}x{max_height}px.")

    if image.mode not in settings.ALLOWED_IMAGE_MODES:
        raise ValidationError(f"Unsupported image mode. Only {', '.join(settings.ALLOWED_IMAGE_MODES)} are allowed.")

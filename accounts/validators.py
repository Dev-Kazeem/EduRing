import uuid

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

MAX_PROFILE_PICTURE_SIZE_MB = 5


def validate_image_file_size(value):
    """Reject uploads over MAX_PROFILE_PICTURE_SIZE_MB. Runs on every save, not just forms."""
    limit_bytes = MAX_PROFILE_PICTURE_SIZE_MB * 1024 * 1024
    if value.size > limit_bytes:
        raise ValidationError(f"Image file too large — max size is {MAX_PROFILE_PICTURE_SIZE_MB}MB.")


@deconstructible
class ProfilePictureUploadPath:
    """
    Builds an unguessable, collision-free upload path instead of trusting the
    original filename (which could contain path-traversal characters, collide
    with another user's file, or leak the uploader's original file naming).
    """

    def __call__(self, instance, filename):
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
        return f"profile_pics/{uuid.uuid4().hex}.{ext}"


profile_picture_upload_path = ProfilePictureUploadPath()

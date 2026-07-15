from io import BytesIO

from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image, ImageOps

from .validators import profile_picture_upload_path, validate_image_file_size

PROFILE_PICTURE_MAX_DIMENSION = 512  # px, longest side after resize


class CustomUser(AbstractUser):
    """
    A single user model shared by both Students and Teachers.
    The `role` field determines which dashboard/permissions the user gets.
    """

    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        TEACHER = 'TEACHER', 'Teacher'

    role = models.CharField(max_length=10, choices=Role.choices)

    # Common optional profile fields
    phone_number = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to=profile_picture_upload_path,
        blank=True,
        null=True,
        validators=[validate_image_file_size],
        help_text=f"JPEG/PNG/WebP, up to 5MB. Auto-resized to {PROFILE_PICTURE_MAX_DIMENSION}px.",
    )

    # Teacher-specific
    department = models.CharField(max_length=100, blank=True, help_text="Teacher's department/subject area")

    # Student-specific
    roll_number = models.CharField(max_length=50, blank=True, help_text="Student ID / roll number")
    grade_level = models.CharField(max_length=50, blank=True, help_text="Class / grade / year")

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    def save(self, *args, **kwargs):
        # Figure out whether the picture is being added/replaced/removed so we
        # can (a) process a genuinely new upload and (b) clean up the old file
        # from storage afterward instead of leaving it orphaned.
        old_picture_name = None
        if self.pk:
            old_picture_name = (
                CustomUser.objects.filter(pk=self.pk)
                .values_list('profile_picture', flat=True)
                .first()
            )

        new_upload = bool(self.profile_picture) and self.profile_picture.name != old_picture_name
        if new_upload:
            self._process_profile_picture()

        super().save(*args, **kwargs)

        current_name = self.profile_picture.name if self.profile_picture else None
        if old_picture_name and old_picture_name != current_name:
            self.__class__.profile_picture.field.storage.delete(old_picture_name)

    def _process_profile_picture(self):
        """
        Normalize an incoming upload before it ever touches storage:
        honor EXIF orientation then strip all EXIF (privacy — phone photos
        often embed GPS coordinates), convert to RGB JPEG, and downscale to
        a sane max size. Works against any storage backend since it operates
        entirely in memory rather than assuming a local filesystem path.
        """
        image = Image.open(self.profile_picture)
        image = ImageOps.exif_transpose(image)  # apply rotation before EXIF is dropped
        image = image.convert('RGB')
        image.thumbnail((PROFILE_PICTURE_MAX_DIMENSION, PROFILE_PICTURE_MAX_DIMENSION), Image.LANCZOS)

        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=85, optimize=True)  # no exif kwarg => EXIF dropped
        buffer.seek(0)

        base_name = self.profile_picture.name.rsplit('.', 1)[0]
        # save(..., save=False) writes the processed bytes to storage under a
        # fresh name right now, without triggering another model save() (which
        # would otherwise recurse back into this same save() override).
        self.profile_picture.save(f"{base_name}.jpg", ContentFile(buffer.read()), save=False)

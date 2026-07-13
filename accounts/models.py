from django.contrib.auth.models import AbstractUser
from django.db import models


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
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

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

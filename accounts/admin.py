from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'roll_number')

    fieldsets = UserAdmin.fieldsets + (
        ('Role & Profile', {
            'fields': (
                'role', 'phone_number', 'bio', 'profile_picture',
                'department', 'roll_number', 'grade_level',
            )
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role', {'fields': ('role', 'email')}),
    )

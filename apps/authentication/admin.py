"""
Django admin configuration for the authentication app.

This module registers the User model with Django's admin interface,
customizing the display and editing capabilities for user management.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the User model.

    This class customizes the Django admin interface for user management,
    defining which fields are displayed, searchable, and editable.
    """

    list_display = ('id', 'email', 'username', 'is_active', 'created_at', 'last_seen')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email', 'username')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Profile', {'fields': ('username',)}),
        ('Status', {'fields': ('is_active',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'last_seen')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('id', 'created_at', 'updated_at')

    def get_readonly_fields(self, request, obj=None):
        """Make ID read-only for existing users."""
        if obj:
            return self.readonly_fields + ('email',)
        return self.readonly_fields

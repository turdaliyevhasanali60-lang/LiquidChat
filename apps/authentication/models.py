"""
Custom User model for LiquidChat.

This module defines the User model that extends Django's AbstractUser,
providing a solid foundation for user authentication and presence tracking.
The model uses UUID as the primary key and includes all necessary fields
for the chat application's user management.
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model for LiquidChat.

    This model extends Django's AbstractUser to provide a UUID-based primary key
    and includes additional fields for presence tracking. The presence status
    (online/offline) is managed through Redis, not the database, for performance.

    Attributes:
        id: UUID primary key for the user
        email: Unique email address used for authentication
        username: Unique display name shown in chat
        password: Hashed password stored securely
        is_active: Boolean indicating if the account is active
        created_at: Timestamp when the account was created
        updated_at: Timestamp of the last account update
        last_seen: Timestamp of the user's last activity
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the user"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="Optional email address"
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Display name shown in chat"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indicates if the user account is active"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the account was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of the last account update"
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the user's last activity"
    )

    # Fields removed from AbstractUser that we don't need
    first_name = None
    last_name = None

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        """Return string representation of the user."""
        return f"{self.username} ({self.email})"

    @property
    def is_online(self):
        """
        Check if the user is currently online.

        This property checks Redis for the user's presence status.
        The actual status is managed by the presence system in Django Channels.

        Returns:
            bool: True if the user is online, False otherwise
        """
        from django.core.cache import cache
        return cache.get(f'user_presence:{self.id}') is not None

    def update_last_seen(self):
        """Update the last_seen timestamp to current time."""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])

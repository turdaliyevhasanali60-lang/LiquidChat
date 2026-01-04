"""Authentication app configuration."""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Configuration for the authentication application.

    This app handles user registration, authentication, and JWT token management.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    verbose_name = 'Authentication'

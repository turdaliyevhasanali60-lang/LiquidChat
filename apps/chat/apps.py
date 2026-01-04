"""Chat app configuration."""

from django.apps import AppConfig


class ChatConfig(AppConfig):
    """Configuration for the chat application.

    This app handles real-time messaging functionality including global chat,
    private conversations, and presence management through Django Channels.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chat'
    verbose_name = 'Chat'

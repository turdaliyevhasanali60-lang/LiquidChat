"""
Django admin configuration for the chat app.

This module registers the chat models with Django's admin interface,
providing management capabilities for conversations and messages.
"""

from django.contrib import admin
from .models import Conversation, PrivateMessage, GlobalMessage


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Conversation model.
    """

    list_display = ('id', 'get_participants', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('id', 'participants__username', 'participants__email')
    filter_horizontal = ('participants',)
    readonly_fields = ('id', 'created_at', 'updated_at')

    def get_participants(self, obj):
        """Get a string representation of participants."""
        return ', '.join([p.username for p in obj.participants.all()])

    get_participants.short_description = 'Participants'


@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    """
    Admin configuration for the PrivateMessage model.
    """

    list_display = ('id', 'sender', 'conversation', 'content_preview', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('content', 'sender__username', 'sender__email')
    readonly_fields = ('id', 'timestamp')
    raw_id_fields = ('conversation', 'sender')

    def content_preview(self, obj):
        """Show a preview of the message content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Content'


@admin.register(GlobalMessage)
class GlobalMessageAdmin(admin.ModelAdmin):
    """
    Admin configuration for the GlobalMessage model.
    """

    list_display = ('id', 'sender', 'content_preview', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('content', 'sender__username', 'sender__email')
    readonly_fields = ('id', 'timestamp')
    raw_id_fields = ('sender',)

    def content_preview(self, obj):
        """Show a preview of the message content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    content_preview.short_description = 'Content'

"""
URL configuration for the chat app.

This module defines URL patterns for all chat-related REST API endpoints
including conversations, messages, and global chat history.
"""

from django.urls import path

from .views import (
    ConversationListView,
    ConversationDetailView,
    ConversationCreateView,
    PrivateMessageHistoryView,
    GlobalMessageHistoryView,
    MarkMessagesReadView,
    GetOrCreateConversationView,
)

app_name = 'chat'

urlpatterns = [
    # Conversation endpoints
    path(
        'conversations/',
        ConversationListView.as_view(),
        name='conversation_list'
    ),
    path(
        'conversations/create/',
        ConversationCreateView.as_view(),
        name='conversation_create'
    ),
    path(
        'conversations/<uuid:conversation_id>/',
        ConversationDetailView.as_view(),
        name='conversation_detail'
    ),
    path(
        'conversations/<uuid:conversation_id>/messages/',
        PrivateMessageHistoryView.as_view(),
        name='message_history'
    ),
    path(
        'conversations/<uuid:conversation_id>/read/',
        MarkMessagesReadView.as_view(),
        name='mark_read'
    ),
    path(
        'conversations/user/<uuid:user_id>/',
        GetOrCreateConversationView.as_view(),
        name='get_or_create_conversation'
    ),

    # Global chat endpoints
    path(
        'global/messages/',
        GlobalMessageHistoryView.as_view(),
        name='global_message_history'
    ),
]

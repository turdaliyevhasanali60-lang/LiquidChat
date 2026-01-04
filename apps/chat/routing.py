"""
WebSocket URL routing for the chat app.

This module defines WebSocket URL patterns and their corresponding consumers.
WebSocket connections use JWT authentication via query string tokens.
"""

from django.urls import re_path

from .consumers import GlobalChatConsumer, PrivateChatConsumer

websocket_urlpatterns = [
    # Global chat WebSocket endpoint
    re_path(
        r'^ws/chat/global/$',
        GlobalChatConsumer.as_asgi()
    ),

    # Private chat WebSocket endpoint
    re_path(
        r'^ws/chat/private/$',
        PrivateChatConsumer.as_asgi()
    ),
]

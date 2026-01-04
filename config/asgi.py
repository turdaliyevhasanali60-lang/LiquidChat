"""
ASGI config for LiquidChat project.

It exposes the ASGI callable as a module-level variable named ``application``.

This module handles both HTTP and WebSocket connections, routing them to the
appropriate applications. The channel layer is configured to use Redis for
distributed real-time communication across multiple server instances.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import after Django is initialized
from apps.chat.routing import websocket_urlpatterns
from apps.chat.middleware import JwtAuthMiddleware

application = ProtocolTypeRouter({
    # HTTP requests are handled by Django's ASGI application
    "http": django_asgi_app,

    # WebSocket connections with authentication and routing
    "websocket": AllowedHostsOriginValidator(
        JwtAuthMiddleware(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        )
    ),
})

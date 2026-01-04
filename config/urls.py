"""
URL configuration for LiquidChat project.

This module defines all URL patterns for the application, including REST API
endpoints for authentication and chat functionality. WebSocket endpoints are
configured in the ASGI application (config/asgi.py).
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication endpoints
    path('api/auth/', include('apps.authentication.urls')),

    # Chat API endpoints
    path('api/chat/', include('apps.chat.urls')),

    # Chat Frontend
    path('', include('apps.chat.urls_frontend')),
]

"""
WSGI config for LiquidChat project.

It exposes the WSGI callable as a module-level variable named ``application``.

This module handles traditional HTTP requests using the WSGI standard.
For WebSocket connections, use the ASGI configuration (config/asgi.py) instead.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

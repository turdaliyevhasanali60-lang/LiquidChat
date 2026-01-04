"""
Custom middleware for WebSocket authentication.

This module provides JWT authentication middleware for Django Channels
WebSocket connections. It validates JWT tokens from the query string
and associates the authenticated user with the WebSocket connection.
"""

import jwt
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

User = get_user_model()


class JwtAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for JWT authentication in WebSocket connections.

    This middleware intercepts WebSocket connection requests and validates
    JWT tokens from the query string. On successful authentication, it
    adds the user object to the connection scope.

    Usage:
        Add this middleware to the ASGI application configuration
        to protect WebSocket endpoints.

    Token Format:
        The token should be passed in the WebSocket URL query string:
        ws://host/ws/chat/?token=<jwt_access_token>
    """

    async def __call__(self, scope, receive, send):
        """
        Process the WebSocket connection request.

        Args:
            scope: ASGI connection scope containing request information
            receive: Callable to receive messages from the client
            send: Callable to send messages to the client
        """
        # Get token from query string
        query_string = scope.get('query_string', b'').decode()
        token = None
        
        print(f"[DEBUG WS] Query String: {query_string}")

        # Parse query parameters to find token
        for param in query_string.split('&'):
            if param.startswith('token='):
                token = param.split('=')[1]
                break
        
        print(f"[DEBUG WS] Token found: {token is not None}")

        # Authenticate user
        if token:
            user = await self.get_user_from_token(token)
            scope['user'] = user
            print(f"[DEBUG WS] User resolved: {user}")
        else:
            scope['user'] = AnonymousUser()
            print("[DEBUG WS] No token, using AnonymousUser")

        return await super().__call__(scope, receive, send)

    async def get_user_from_token(self, token):
        """
        Validate JWT token and return the corresponding user.

        Args:
            token: JWT access token string

        Returns:
            User: The authenticated user object, or AnonymousUser if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256']
            )
            print(f"[DEBUG WS] Decoded payload: {payload}")
            user_id = payload.get('user_id') or payload.get('id')
            if user_id:
                user = await self.get_user(user_id)
                if user and user.is_active:
                    return user
        except jwt.ExpiredSignatureError:
            pass
        except jwt.InvalidTokenError:
            pass

        return AnonymousUser()

    @database_sync_to_async
    def get_user(self, user_id):
        """
        Fetch user from database asynchronously.

        Args:
            user_id: UUID of the user to fetch

        Returns:
            User: The user object if found and active, None otherwise
        """
        try:
            return User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return None


class JwtAuthMiddlewareStack:
    """
    Convenience wrapper for JwtAuthMiddleware.

    This class provides a simple way to apply JWT authentication to
    WebSocket URL routing configurations.
    """

    def __init__(self, inner):
        """Initialize the middleware stack."""
        self.inner = inner

    async def __call__(self, scope, receive, send):
        """
        Apply JWT authentication and call inner application.

        Args:
            scope: ASGI connection scope
            receive: Callable to receive messages
            send: Callable to send messages
        """
        # Create middleware instance
        middleware = JwtAuthMiddleware(self.inner)
        return await middleware(scope, receive, send)

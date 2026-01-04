"""
Views for the authentication app.

This module provides REST API views for user authentication operations including
registration, login, logout, and user discovery. All views use JWT authentication.
"""

from django.contrib.auth import logout
from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserSerializer,
    LogoutSerializer,
)


class UserRegistrationView(CreateAPIView):
    """
    API endpoint for user registration.

    Creates a new user account with the provided email, username, and password.
    Returns JWT tokens upon successful registration.

    Methods:
        POST: Create a new user account

    Response:
        201: User created successfully with tokens
        400: Validation errors
    """

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Create a new user and return JWT tokens."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


class UserLoginView(APIView):
    """
    API endpoint for user login.

    Authenticates user credentials and returns JWT access and refresh tokens.

    Methods:
        POST: Authenticate and return tokens

    Response:
        200: Login successful with tokens
        401: Invalid credentials
        400: Validation errors
    """

    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        """Authenticate user and return JWT tokens."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    """
    API endpoint for token refresh.

    Refreshes the access token using a valid refresh token.

    Methods:
        POST: Refresh access token

    Response:
        200: New access token
        401: Invalid refresh token
    """

    permission_classes = [AllowAny]


class LogoutView(APIView):
    """
    API endpoint for user logout.

    Blacklists the refresh token and closes the WebSocket connection.

    Methods:
        POST: Logout user and blacklist token

    Response:
        200: Logout successful
        400: Invalid token
    """

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        """Blacklist refresh token and logout user."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data['refresh']

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Update last seen
            request.user.update_last_seen()

            # Logout from Django
            logout(request)

            return Response(
                {'detail': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'detail': 'Invalid token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserListView(ListAPIView):
    """
    API endpoint for user discovery.

    Returns a list of users that can be used for starting private conversations.
    Supports search by username or email.

    Methods:
        GET: List users with optional search

    Query Parameters:
        search: Optional search term to filter users

    Response:
        200: List of users
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return users filtered by search query."""
        queryset = User.objects.filter(is_active=True).exclude(
            id=self.request.user.id
        )

        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                username__icontains=search
            ) | queryset.filter(
                email__icontains=search
            )

        return queryset.order_by('username')

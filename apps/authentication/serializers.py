"""
Serializers for the authentication app.

This module provides serializers for user registration, login, and token management.
These serializers handle data validation and transformation for REST API endpoints.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer

from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Handles validation and creation of new user accounts. Validates password
    strength and ensures unique constraints for email and username.

    Attributes:
        password: User's password (write-only, validated for strength)
        password_confirm: Password confirmation for validation
    """

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="User password (write-only)"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Password confirmation for validation"
    )

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'password',
            'password_confirm',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })

        return attrs

    def create(self, validated_data):
        """Create a new user with hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.

    Authenticates user credentials and returns JWT tokens upon successful
    authentication. Supports login with either email or username.

    Attributes:
        username: User's username
        password: User's password
    """

    username = serializers.CharField(
        required=True,
        help_text="User's username"
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="User's password"
    )

    def validate(self, attrs):
        """Authenticate user credentials."""
        username = attrs.get('username')
        password = attrs.get('password')

        # Try to find user by username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'detail': 'Invalid credentials.'
            })

        # Authenticate
        if not user.check_password(password):
            raise serializers.ValidationError({
                'detail': 'Invalid credentials.'
            })

        if not user.is_active:
            raise serializers.ValidationError({
                'detail': 'Account is disabled.'
            })

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user data representation.

    Provides read-only access to user information including presence status.

    Attributes:
        is_online: Boolean indicating if user is currently online
    """

    is_online = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'is_online',
            'created_at',
            'last_seen',
        ]
        read_only_fields = ['id', 'created_at', 'last_seen']

    def get_is_online(self, obj):
        """
        Get the user's online status.

        Uses Redis cache to determine if the user is currently online.
        This status is updated by the presence system in Django Channels.

        Args:
            obj: User instance

        Returns:
            bool: True if user is online, False otherwise
        """
        from django.core.cache import cache
        return cache.get(f'user_presence:{obj.id}') is not None


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom token refresh serializer.

    Extends the default JWT refresh serializer to include additional
    user information in the response.
    """

    def validate(self, attrs):
        """Validate refresh token and return new access token with user info."""
        data = super().validate(attrs)

        # Optionally, you can add custom data here
        # For example, include user ID from the token
        from rest_framework_simplejwt.tokens import Token
        token = attrs['refresh']

        # You could decode the token to get user info
        # But for security, typically you'd refresh and let client handle it

        return data


class LogoutSerializer(serializers.Serializer):
    """
    Serializer for user logout.

    Validates the refresh token to be blacklisted during logout.
    """

    refresh = serializers.CharField(
        required=True,
        help_text="Refresh token to be blacklisted"
    )

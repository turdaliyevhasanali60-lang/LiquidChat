"""
Custom exception handling for the REST API.

This module provides a custom exception handler that formats error responses
consistently across the LiquidChat API. It extends Django REST Framework's
default exception handling with additional error types and standardized
response formats.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler for the API.

    This handler extends the default DRF exception handler to provide
    consistent error response formatting. All errors are returned with
    a standard format including error type and details.

    Args:
        exc: The exception that was raised
        context: Additional context including the view and request

    Returns:
        Response: A standardized error response
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Customize the response format
        custom_response_data = {
            'error': {
                'status_code': response.status_code,
                'message': get_error_message(response.data),
                'details': response.data,
            }
        }
        response.data = custom_response_data

    return response


def get_error_message(data):
    """
    Extract a human-readable error message from response data.

    Args:
        data: Error response data (dict or list)

    Returns:
        str: A human-readable error message
    """
    if isinstance(data, dict):
        # Handle validation errors with field names
        if 'detail' in data:
            return str(data['detail'])

        # Handle field validation errors
        messages = []
        for field, errors in data.items():
            if isinstance(errors, list):
                for error in errors:
                    messages.append(f"{field}: {error}")
            else:
                messages.append(f"{field}: {errors}")

        return '; '.join(messages) if messages else 'An error occurred'

    elif isinstance(data, list) and len(data) > 0:
        return str(data[0])

    return 'An error occurred'


class APIError(Exception):
    """
    Base exception for API errors.

    All custom API exceptions should inherit from this class.
    It provides a standard way to define error messages and status codes.
    """

    default_message = 'An API error occurred'
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message=None, status_code=None):
        """Initialize the exception."""
        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)

    def __str__(self):
        """Return string representation."""
        return self.message


class AuthenticationError(APIError):
    """Exception raised for authentication failures."""

    default_message = 'Authentication failed'
    status_code = status.HTTP_401_UNAUTHORIZED


class ValidationError(APIError):
    """Exception raised for validation failures."""

    default_message = 'Validation error'
    status_code = status.HTTP_400_BAD_REQUEST


class NotFoundError(APIError):
    """Exception raised when a resource is not found."""

    default_message = 'Resource not found'
    status_code = status.HTTP_404_NOT_FOUND


class PermissionDeniedError(APIError):
    """Exception raised when permission is denied."""

    default_message = 'Permission denied'
    status_code = status.HTTP_403_FORBIDDEN


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded."""

    default_message = 'Rate limit exceeded'
    status_code = status.HTTP_429_TOO_MANY_REQUESTS

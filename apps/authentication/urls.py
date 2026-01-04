"""
URL configuration for the authentication app.

This module defines URL patterns for all authentication-related endpoints
including registration, login, logout, and user discovery.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserRegistrationView,
    UserLoginView,
    LogoutView,
    UserListView,
)

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('signup/', UserRegistrationView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User discovery
    path('users/', UserListView.as_view(), name='user_list'),
]

"""
Tests for authentication app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class UserModelTest(TestCase):
    """Test the User model."""

    def test_create_user(self):
        """Test creating a user."""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)


class AuthenticationAPITest(APITestCase):
    """Test authentication API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.signup_url = '/api/auth/signup/'
        self.login_url = '/api/auth/login/'
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }

    def test_user_signup(self):
        """Test user registration."""
        response = self.client.post(self.signup_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_user_login(self):
        """Test user login."""
        # Create user first (without password_confirm)
        User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        
        # Test login
        login_data = {
            'email_or_username': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_duplicate_email_signup(self):
        """Test signup with duplicate email."""
        # Create user first (without password_confirm)
        User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        response = self.client.post(self.signup_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

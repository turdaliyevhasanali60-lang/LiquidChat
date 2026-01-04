"""
Tests for chat app.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.chat.models import GlobalMessage, Conversation, PrivateMessage

User = get_user_model()


class GlobalMessageTest(TestCase):
    """Test GlobalMessage model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_create_global_message(self):
        """Test creating a global message."""
        message = GlobalMessage.objects.create(
            sender=self.user,
            content='Test message'
        )
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.content, 'Test message')
        self.assertIsNotNone(message.timestamp)


class ConversationTest(TestCase):
    """Test Conversation model."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='testpass123'
        )

    def test_create_conversation(self):
        """Test creating a conversation."""
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)
        
        self.assertEqual(conversation.participants.count(), 2)
        self.assertIn(self.user1, conversation.participants.all())
        self.assertIn(self.user2, conversation.participants.all())


class PrivateMessageTest(TestCase):
    """Test PrivateMessage model."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            username='user2',
            password='testpass123'
        )
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

    def test_create_private_message(self):
        """Test creating a private message."""
        message = PrivateMessage.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content='Private test message'
        )
        self.assertEqual(message.sender, self.user1)
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.content, 'Private test message')
        self.assertFalse(message.is_read)

"""
Models for the chat app.

This module defines the database models for LiquidChat's messaging system.
It includes models for private conversations and messages, as well as
global chat messages. All models use UUID for unique identification.
"""

import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Conversation(models.Model):
    """
    Model representing a private conversation between two users.

    Each pair of users has exactly one conversation. This model tracks
    the conversation metadata and timestamps for sorting and display.

    Attributes:
        id: UUID primary key for the conversation
        participants: Many-to-many relationship with User model
        created_at: Timestamp when the conversation was created
        updated_at: Timestamp of the last message in the conversation
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the conversation"
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conversations',
        help_text="Users participating in this conversation"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the conversation was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of the last message in the conversation"
    )

    class Meta:
        db_table = 'conversations'
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['id'],
                name='unique_conversation_id'
            )
        ]

    def __str__(self):
        """Return string representation of the conversation."""
        participants_list = self.participants.all()
        if participants_list.count() == 2:
            return f"Conversation between {participants_list[0].username} and {participants_list[1].username}"
        return f"Conversation {self.id}"

    def get_other_user(self, user):
        """Get the other participant in a two-user conversation."""
        return self.participants.exclude(id=user.id).first()


class PrivateMessage(models.Model):
    """
    Model representing a private message within a conversation.

    Messages belong to a conversation and are sent by a specific user.
    The model tracks read status for message delivery confirmation.

    Attributes:
        id: UUID primary key for the message
        conversation: Foreign key to the Conversation model
        sender: Foreign key to the User model
        content: Text content of the message
        timestamp: When the message was sent
        is_read: Whether the message has been read by the recipient
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the message"
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Conversation this message belongs to"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text="User who sent the message"
    )
    content = models.TextField(
        max_length=2000,
        help_text="Message content (max 2000 characters)"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the message was sent"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the message has been read"
    )

    class Meta:
        db_table = 'private_messages'
        verbose_name = 'Private Message'
        verbose_name_plural = 'Private Messages'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender', 'timestamp']),
        ]

    def __str__(self):
        """Return string representation of the message."""
        return f"Message from {self.sender.username} at {self.timestamp}"

    def to_dict(self):
        """Convert message to dictionary for JSON serialization."""
        return {
            'id': str(self.id),
            'conversation_id': str(self.conversation_id),
            'sender': {
                'id': str(self.sender.id),
                'username': self.sender.username,
            },
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read,
        }


class GlobalMessage(models.Model):
    """
    Model representing a message in the global chat room.

    Global messages are visible to all users in the global chat.
    This model is optimized for high-volume message storage.

    Attributes:
        id: Auto-increment primary key for performance
        sender: Foreign key to the User model
        content: Text content of the message
        timestamp: When the message was sent
    """

    id = models.BigAutoField(
        primary_key=True,
        help_text="Auto-increment ID for performance"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='global_messages',
        help_text="User who sent the message"
    )
    content = models.TextField(
        max_length=2000,
        help_text="Message content (max 2000 characters)"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the message was sent"
    )

    class Meta:
        db_table = 'global_messages'
        verbose_name = 'Global Message'
        verbose_name_plural = 'Global Messages'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        """Return string representation of the message."""
        return f"Global message from {self.sender.username} at {self.timestamp}"

    def to_dict(self):
        """Convert message to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'sender': {
                'id': str(self.sender.id),
                'username': self.sender.username,
            },
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
        }

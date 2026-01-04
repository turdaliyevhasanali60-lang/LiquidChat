"""
Serializers for the chat app.

This module provides serializers for conversations and messages.
These serializers handle data validation and transformation for REST API endpoints.
"""

from rest_framework import serializers

from apps.authentication.serializers import UserSerializer
from .models import Conversation, PrivateMessage, GlobalMessage


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for conversation metadata.

    Provides read-only access to conversation information including
    participants and last message timestamp.
    """

    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'participants',
            'created_at',
            'updated_at',
            'last_message',
            'unread_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        """Get the last message in the conversation."""
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return {
                'content': last_msg.content[:100],
                'timestamp': last_msg.timestamp.isoformat(),
                'sender_id': str(last_msg.sender_id),
            }
        return None

    def get_unread_count(self, obj):
        """Get count of unread messages for the current user."""
        request = self.context.get('request')
        if request and request.user:
            return obj.messages.filter(
                is_read=False
            ).exclude(
                sender=request.user
            ).count()
        return 0


class ConversationCreateSerializer(serializers.Serializer):
    """
    Serializer for creating or getting a conversation.

    Used to find or create a private conversation with another user.
    """

    user_id = serializers.UUIDField(
        required=True,
        help_text="UUID of the user to start a conversation with"
    )

    def validate_user_id(self, value):
        """Validate that the user exists."""
        from apps.authentication.models import User
        try:
            User.objects.get(id=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found or inactive.")
        return value

    def create(self, validated_data):
        """Create or get existing conversation."""
        from apps.authentication.models import User
        user_id = validated_data['user_id']
        current_user = self.context['request'].user

        other_user = User.objects.get(id=user_id)

        # Check if conversation already exists
        conversation = Conversation.objects.filter(
            participants=current_user
        ).filter(
            participants=other_user
        ).first()

        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(current_user, other_user)

        return conversation


class PrivateMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for private messages.

    Provides full serialization of private message data including
    sender information and read status.
    """

    sender = UserSerializer(read_only=True)

    class Meta:
        model = PrivateMessage
        fields = [
            'id',
            'conversation',
            'sender',
            'content',
            'timestamp',
            'is_read',
        ]
        read_only_fields = ['id', 'conversation', 'sender', 'timestamp', 'is_read']


class PrivateMessageCreateSerializer(serializers.Serializer):
    """
    Serializer for creating private messages via REST API.

    Used for sending messages through the REST API (not WebSocket).
    """

    content = serializers.CharField(
        max_length=2000,
        required=True,
        help_text="Message content (max 2000 characters)"
    )


class GlobalMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for global messages.

    Provides serialization of global chat message data including
    sender information.
    """

    sender = UserSerializer(read_only=True)

    class Meta:
        model = GlobalMessage
        fields = [
            'id',
            'sender',
            'content',
            'timestamp',
        ]
        read_only_fields = ['id', 'sender', 'timestamp']


class MessageMarkReadSerializer(serializers.Serializer):
    """
    Serializer for marking messages as read.

    Used to update message read status via REST API.
    """

    message_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        help_text="List of message IDs to mark as read"
    )

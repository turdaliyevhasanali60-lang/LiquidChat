"""
Views for the chat app.

This module provides REST API views for conversations and message management.
These views handle CRUD operations for conversations and message history retrieval.
"""

from django.db.models import Q
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, PrivateMessage, GlobalMessage
from .serializers import (
    ConversationSerializer,
    ConversationCreateSerializer,
    PrivateMessageSerializer,
    GlobalMessageSerializer,
)
from django.shortcuts import render

def index(request):
    """Render the main chat application."""
    return render(request, 'chat/index.html')


class ConversationListView(generics.ListAPIView):
    """
    API endpoint for listing user's conversations.

    Returns a list of all conversations the authenticated user is participating in,
    ordered by most recently updated.

    Methods:
        GET: List all conversations

    Response:
        200: List of conversations with participants and last message info
    """

    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return conversations for the current user."""
        user = self.request.user
        return Conversation.objects.filter(
            participants=user
        ).order_by('-updated_at')


class ConversationDetailView(generics.RetrieveAPIView):
    """
    API endpoint for conversation details and messages.

    Returns conversation metadata and messages for a specific conversation.

    Methods:
        GET: Get conversation details and messages

    URL Parameters:
        pk: Conversation UUID

    Response:
        200: Conversation details with messages
        404: Conversation not found
    """

    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return conversations the user participates in."""
        user = self.request.user
        return Conversation.objects.filter(participants=user)

    def retrieve(self, request, *args, **kwargs):
        """Get conversation with messages."""
        instance = self.get_object()

        # Get messages
        messages = PrivateMessage.objects.filter(
            conversation=instance
        ).order_by('timestamp')

        # Serialize data
        conversation_data = ConversationSerializer(instance, context={'request': request}).data
        messages_data = PrivateMessageSerializer(messages, many=True).data

        return Response({
            'conversation': conversation_data,
            'messages': messages_data,
        })


class ConversationCreateView(APIView):
    """
    API endpoint for creating or getting a conversation.

    Creates a new conversation with another user or returns an existing one
    if it already exists.

    Methods:
        POST: Create or get a conversation

    Request Body:
        user_id: UUID of the user to start a conversation with

    Response:
        200: Existing or newly created conversation
        400: Validation error
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Create or get a conversation with another user."""
        serializer = ConversationCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()

        # Get messages for the conversation
        messages = PrivateMessage.objects.filter(
            conversation=conversation
        ).order_by('timestamp')

        return Response({
            'conversation': ConversationSerializer(
                conversation,
                context={'request': request}
            ).data,
            'messages': PrivateMessageSerializer(messages, many=True).data,
        })


class PrivateMessageHistoryView(generics.ListAPIView):
    """
    API endpoint for private message history.

    Returns paginated messages for a specific conversation.

    Methods:
        GET: Get message history

    URL Parameters:
        conversation_id: Conversation UUID

    Query Parameters:
        limit: Maximum number of messages (default 50)
        before: Get messages before this timestamp

    Response:
        200: List of messages
        404: Conversation not found
    """

    serializer_class = PrivateMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get messages for the conversation."""
        conversation_id = self.kwargs['conversation_id']
        user = self.request.user

        # Verify user is a participant
        conversation = Conversation.objects.filter(
            id=conversation_id,
            participants=user
        ).first()

        if not conversation:
            return PrivateMessage.objects.none()

        return PrivateMessage.objects.filter(
            conversation=conversation
        ).order_by('-timestamp')

    def list(self, request, *args, **kwargs):
        """Override list to return in chronological order."""
        queryset = self.get_queryset()
        # Reverse to show oldest first
        messages = list(queryset)[::-1]

        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


class GlobalMessageHistoryView(generics.ListAPIView):
    """
    API endpoint for global message history.

    Returns paginated messages from the global chat room.

    Methods:
        GET: Get global message history

    Query Parameters:
        limit: Maximum number of messages (default 50)
        before: Get messages before this timestamp

    Response:
        200: List of global messages
    """

    serializer_class = GlobalMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get global messages."""
        return GlobalMessage.objects.all().order_by('-timestamp')

    def list(self, request, *args, **kwargs):
        """Override list to return in chronological order."""
        queryset = self.get_queryset()
        # Reverse to show oldest first
        messages = list(queryset)[::-1]

        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


class MarkMessagesReadView(APIView):
    """
    API endpoint for marking messages as read.

    Marks multiple messages as read in a conversation.

    Methods:
        POST: Mark messages as read

    Request Body:
        message_ids: List of message UUIDs to mark as read

    Response:
        200: Success response
        400: Validation error
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Mark messages as read."""
        conversation_id = kwargs.get('conversation_id')
        message_ids = request.data.get('message_ids', [])

        if not message_ids:
            return Response(
                {'detail': 'No message IDs provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify user is a participant
        conversation = Conversation.objects.filter(
            id=conversation_id,
            participants=request.user
        ).first()

        if not conversation:
            return Response(
                {'detail': 'Conversation not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Mark messages as read
        PrivateMessage.objects.filter(
            id__in=message_ids,
            conversation=conversation,
            is_read=False,
        ).exclude(sender=request.user).update(is_read=True)

        return Response({'detail': 'Messages marked as read.'})


class GetOrCreateConversationView(APIView):
    """
    API endpoint for getting or creating a conversation with a specific user.

    This is a convenience endpoint that combines finding or creating a conversation
    with another user and returning the conversation details along with messages.

    Methods:
        GET: Get or create conversation with a user

    URL Parameters:
        user_id: UUID of the other user

    Response:
        200: Conversation details with messages
        400: Validation error
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """Get or create conversation with a user."""
        user = request.user

        # Find existing 2-person conversation
        from django.db.models import Count
        conversation = Conversation.objects.annotate(
            num_participants=Count('participants')
        ).filter(
            num_participants=2,
            participants=user
        ).filter(
            participants__id=user_id
        ).first()

        if not conversation:
            # Create new conversation
            from apps.authentication.models import User
            try:
                other_user = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                return Response(
                    {'detail': 'User not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            conversation = Conversation.objects.create()
            conversation.participants.add(user, other_user)

        # Get messages
        messages = PrivateMessage.objects.filter(
            conversation=conversation
        ).order_by('timestamp')

        return Response({
            'conversation': ConversationSerializer(
                conversation,
                context={'request': request}
            ).data,
            'messages': PrivateMessageSerializer(messages, many=True).data,
        })

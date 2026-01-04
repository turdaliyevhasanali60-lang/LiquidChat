"""
Django Channels consumers for real-time chat.

This module provides WebSocket consumers for global and private chat functionality.
Consumers handle WebSocket connections, message routing, presence management,
and integration with the Django ORM through asynchronous methods.
"""

import json
import bleach
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .models import Conversation, PrivateMessage, GlobalMessage
from apps.authentication.models import User


class GlobalChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer for the global chat room.

    This consumer handles WebSocket connections for the public chat room
    where all users can send and receive messages. Messages are broadcast
    to all connected clients in real-time.

    WebSocket Events:
        send_global_message: Client sends a message to the global chat
        global_message: Server broadcasts a message to all clients
        user_presence: Server notifies about user online/offline status
    """

    async def connect(self):
        """
        Handle WebSocket connection.

        Adds the user to the global chat group and broadcasts their
        online status to all connected clients.
        """
        if self.scope['user'].is_anonymous:
            await self.close(code=4001)
            return

        self.user = self.scope['user']
        self.group_name = 'global_chat'

        # Join global chat group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Mark user as online
        await self.set_user_online(self.user.id)

        # Accept the connection
        await self.accept()

        # Broadcast user joined
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'user_presence',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'status': 'online',
            }
        )

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.

        Removes the user from the global chat group and broadcasts their
        offline status. Updates the user's last_seen timestamp.
        """
        if hasattr(self, 'user') and self.user and not self.user.is_anonymous:
            # Leave global chat group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

            # Mark user as offline
            await self.set_user_offline(self.user.id)

            # Update last seen
            await self.update_user_last_seen(self.user.id)

            # Broadcast user left
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'user_presence',
                    'user_id': str(self.user.id),
                    'username': self.user.username,
                    'status': 'offline',
                }
            )

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.

        Processes client messages and broadcasts them to the global chat.
        """
        if self.scope['user'].is_anonymous:
            return

        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'send_global_message':
                content = data.get('content', '').strip()

                if not content:
                    return

                # Sanitize content
                content = self.sanitize_content(content)

                # Validate length
                if len(content) > settings.MESSAGE_MAX_LENGTH:
                    content = content[:settings.MESSAGE_MAX_LENGTH]

                # Save message to database
                message = await self.save_global_message(self.user.id, content)

                # Broadcast to all users in the group
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'global_message',
                        'message': {
                            'id': message['id'],
                            'sender': {
                                'id': str(self.user.id),
                                'username': self.user.username,
                            },
                            'content': content,
                            'timestamp': message['timestamp'],
                        },
                    }
                )

        except json.JSONDecodeError:
            pass

    async def global_message(self, event):
        """
        Send global message to WebSocket.

        This handler is called when the global chat group broadcasts
        a new message.
        """
        await self.send(text_data=json.dumps({
            'type': 'global_message',
            'message': event['message'],
        }))

    async def user_presence(self, event):
        """
        Send presence update to WebSocket.

        This handler is called when a user's online/offline status changes.
        """
        # Don't send presence update for self
        if event.get('user_id') == str(self.user.id):
            return

        await self.send(text_data=json.dumps({
            'type': 'user_presence',
            'user_id': event['user_id'],
            'username': event['username'],
            'status': event['status'],
        }))

    @database_sync_to_async
    def set_user_online(self, user_id):
        """Mark user as online in Redis."""
        cache.set(f'user_presence:{user_id}', True, settings.PRESENCE_EXPIRY)

    @database_sync_to_async
    def set_user_offline(self, user_id):
        """Mark user as offline in Redis."""
        cache.delete(f'user_presence:{user_id}')

    @database_sync_to_async
    def update_user_last_seen(self, user_id):
        """Update user's last seen timestamp."""
        User.objects.filter(id=user_id).update(last_seen=timezone.now())

    @database_sync_to_async
    def save_global_message(self, user_id, content):
        """Save global message to database and return it."""
        user = User.objects.get(id=user_id)
        message = GlobalMessage.objects.create(
            sender=user,
            content=content,
        )
        return {
            'id': message.id,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
        }

    def sanitize_content(self, content):
        """Sanitize message content to prevent XSS."""
        return bleach.clean(
            content,
            tags=[],
            strip=True,
        )


class PrivateChatConsumer(AsyncWebsocketConsumer):
    """
    Consumer for private direct messaging.

    This consumer handles WebSocket connections for private conversations
    between two users. Messages are sent directly to the recipient and
    persisted in the database.

    WebSocket Events:
        send_private_message: Client sends a private message
        private_message: Server delivers a private message
        user_presence: Server notifies about user online/offline status
        typing_indicator: Server forwards typing indicators
    """

    async def connect(self):
        """
        Handle WebSocket connection.

        Connects the user to their personal inbox channel for receiving
        private messages.
        """
        if self.scope['user'].is_anonymous:
            await self.close(code=4001)
            return

        self.user = self.scope['user']
        self.group_name = f'user_{self.user.id}'

        # Join personal inbox group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Mark user as online
        await self.set_user_online(self.user.id)

        # Accept the connection
        await self.accept()

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.

        Removes the user from their personal inbox channel and marks
        them as offline.
        """
        if hasattr(self, 'user') and self.user and not self.user.is_anonymous:
            # Leave personal inbox group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

            # Mark user as offline
            await self.set_user_offline(self.user.id)

            # Update last seen
            await self.update_user_last_seen(self.user.id)

    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages.

        Processes private message sends and typing indicators.
        """
        if self.scope['user'].is_anonymous:
            return

        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'send_private_message':
                conversation_id = data.get('conversation_id')
                content = data.get('content', '').strip()

                if not conversation_id or not content:
                    return

                # Sanitize and validate content
                content = self.sanitize_content(content)
                if len(content) > settings.MESSAGE_MAX_LENGTH:
                    content = content[:settings.MESSAGE_MAX_LENGTH]

                # Save message and deliver to recipient
                message = await self.send_private_message(
                    self.user.id,
                    conversation_id,
                    content
                )

                # Get conversation to find recipient
                conversation = await self.get_conversation(conversation_id)
                if conversation:
                    recipient_id = await self.get_recipient_id(
                        conversation_id,
                        self.user.id
                    )

                    if recipient_id:
                        print(f"[DEBUG WS] Forwarding message to recipient: {recipient_id}")
                        # Send to recipient's inbox
                        await self.channel_layer.group_send(
                            f'user_{recipient_id}',
                            {
                                'type': 'private_message',
                                'message': message,
                            }
                        )

                        # Confirm to sender
                        await self.send(text_data=json.dumps({
                            'type': 'private_message_sent',
                            'message': message,
                        }))
                    else:
                        print(f"[DEBUG WS] Recipient not found for conversation {conversation_id}")

            elif message_type == 'typing_start':
                conversation_id = data.get('conversation_id')
                if conversation_id:
                    conversation = await self.get_conversation(conversation_id)
                    if conversation:
                        recipient_id = await self.get_recipient_id(
                            conversation_id,
                            self.user.id
                        )
                        if recipient_id:
                            await self.channel_layer.group_send(
                                f'user_{recipient_id}',
                                {
                                    'type': 'typing_indicator',
                                    'user_id': str(self.user.id),
                                    'username': self.user.username,
                                    'conversation_id': conversation_id,
                                    'status': 'typing',
                                }
                            )

            elif message_type == 'typing_stop':
                conversation_id = data.get('conversation_id')
                if conversation_id:
                    conversation = await self.get_conversation(conversation_id)
                    if conversation:
                        recipient_id = await self.get_recipient_id(
                            conversation_id,
                            self.user.id
                        )
                        if recipient_id:
                            await self.channel_layer.group_send(
                                f'user_{recipient_id}',
                                {
                                    'type': 'typing_indicator',
                                    'user_id': str(self.user.id),
                                    'username': self.user.username,
                                    'conversation_id': conversation_id,
                                    'status': 'stopped',
                                }
                            )

        except json.JSONDecodeError:
            pass

    async def private_message(self, event):
        """
        Send private message to WebSocket.

        This handler is called when a private message is sent to the user.
        """
        await self.send(text_data=json.dumps({
            'type': 'private_message',
            'message': event['message'],
        }))

    async def typing_indicator(self, event):
        """
        Send typing indicator to WebSocket.

        This handler is called when a user starts or stops typing.
        """
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'user_id': event['user_id'],
            'username': event['username'],
            'conversation_id': event['conversation_id'],
            'status': event['status'],
        }))

    @database_sync_to_async
    def set_user_online(self, user_id):
        """Mark user as online in Redis."""
        cache.set(f'user_presence:{user_id}', True, settings.PRESENCE_EXPIRY)

    @database_sync_to_async
    def set_user_offline(self, user_id):
        """Mark user as offline in Redis."""
        cache.delete(f'user_presence:{user_id}')

    @database_sync_to_async
    def update_user_last_seen(self, user_id):
        """Update user's last seen timestamp."""
        User.objects.filter(id=user_id).update(last_seen=timezone.now())

    @database_sync_to_async
    def get_conversation(self, conversation_id):
        """Get conversation by ID."""
        try:
            return Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def get_recipient_id(self, conversation_id, current_user_id):
        """Get the other participant's ID in a conversation."""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            other_user = conversation.participants.exclude(id=current_user_id).first()
            return str(other_user.id) if other_user else None
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def send_private_message(self, user_id, conversation_id, content):
        """Save private message to database."""
        user = User.objects.get(id=user_id)
        conversation = Conversation.objects.get(id=conversation_id)

        message = PrivateMessage.objects.create(
            conversation=conversation,
            sender=user,
            content=content,
        )

        # Update conversation timestamp
        conversation.save(update_fields=['updated_at'])

        return {
            'id': str(message.id),
            'conversation_id': str(conversation_id),
            'sender': {
                'id': str(user.id),
                'username': user.username,
            },
            'content': content,
            'timestamp': message.timestamp.isoformat(),
        }

    def sanitize_content(self, content):
        """Sanitize message content to prevent XSS."""
        return bleach.clean(
            content,
            tags=[],
            strip=True,
        )

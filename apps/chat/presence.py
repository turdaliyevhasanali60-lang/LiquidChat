"""
Presence management utilities.

This module provides helper functions for managing user online/offline status
using Redis. The presence system is used by Django Channels consumers to track
which users are currently connected to the application.
"""

import asyncio
from django.conf import settings
from django.core.cache import cache


def set_user_online(user_id):
    """
    Mark a user as online in Redis.

    This function sets a key in Redis to indicate that a user is currently
    online. The key has a TTL to handle stale connections.

    Args:
        user_id: UUID of the user to mark as online

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cache.set(
            f'user_presence:{user_id}',
            True,
            settings.PRESENCE_EXPIRY
        )
        return True
    except Exception:
        return False


def set_user_offline(user_id):
    """
    Mark a user as offline in Redis.

    This function removes the presence key from Redis to indicate that
    a user is no longer online.

    Args:
        user_id: UUID of the user to mark as offline

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cache.delete(f'user_presence:{user_id}')
        return True
    except Exception:
        return False


def is_user_online(user_id):
    """
    Check if a user is currently online.

    This function checks Redis for the user's presence key to determine
    if they are currently connected.

    Args:
        user_id: UUID of the user to check

    Returns:
        bool: True if the user is online, False otherwise
    """
    try:
        return cache.get(f'user_presence:{user_id}') is not None
    except Exception:
        return False


def get_online_users(user_ids):
    """
    Check online status for multiple users.

    This function efficiently checks the online status of multiple users
    using Redis's mget functionality.

    Args:
        user_ids: List of user UUIDs to check

    Returns:
        dict: Mapping of user_id to online status (bool)
    """
    try:
        keys = [f'user_presence:{uid}' for uid in user_ids]
        values = cache.get_many(keys)

        online_status = {}
        for user_id in user_ids:
            key = f'user_presence:{user_id}'
            online_status[user_id] = key in values and values[key] is True

        return online_status
    except Exception:
        # Return all as offline on error
        return {uid: False for uid in user_ids}


def refresh_user_presence(user_id):
    """
    Refresh a user's presence TTL.

    This function extends the TTL of a user's presence key, effectively
    acting as a heartbeat to keep the user marked as online.

    Args:
        user_id: UUID of the user

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        return set_user_online(user_id)
    except Exception:
        return False


async def async_set_user_online(user_id, channel_layer, channel_name):
    """
    Asynchronously set user online and broadcast to groups.

    This is an async version of set_user_online that also broadcasts
    the online status to relevant groups.

    Args:
        user_id: UUID of the user
        channel_layer: Django Channels layer
        channel_name: Channel name to broadcast from
    """
    set_user_online(user_id)

    # Broadcast presence update
    await channel_layer.group_send(
        'global_chat',
        {
            'type': 'user_presence',
            'user_id': str(user_id),
            'status': 'online',
        }
    )


async def async_set_user_offline(user_id, channel_layer, channel_name):
    """
    Asynchronously set user offline and broadcast to groups.

    This is an async version of set_user_offline that also broadcasts
    the offline status to relevant groups.

    Args:
        user_id: UUID of the user
        channel_layer: Django Channels layer
        channel_name: Channel name to broadcast from
    """
    set_user_offline(user_id)

    # Broadcast presence update
    await channel_layer.group_send(
        'global_chat',
        {
            'type': 'user_presence',
            'user_id': str(user_id),
            'status': 'offline',
        }
    )

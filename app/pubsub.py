"""Pub/Sub state management for Redis clients."""

import asyncio
import logging
from typing import Any

from app.resp import RESPEncoder

logger = logging.getLogger(__name__)


class PubSubContext:
    """
    Manages Pub/Sub state for a single connection.

    Tracks the channels a client is subscribed to.
    """

    def __init__(self):
        """Initialize Pub/Sub context."""
        self._subscribed_channels: set[str] = set()
        self.writer: asyncio.StreamWriter | None = None

    @property
    def subscribed_channels(self) -> set[str]:
        """Get the set of channels the client is subscribed to."""
        return self._subscribed_channels

    @property
    def channel_count(self) -> int:
        """Get the number of channels the client is subscribed to."""
        return len(self._subscribed_channels)

    @property
    def is_in_subscribed_mode(self) -> bool:
        """Check if the client is currently in "subscribed mode"."""
        return self.channel_count > 0

    def subscribe(self, channel: str) -> int:
        """
        Subscribe to a channel.

        Args:
            channel: The channel name to subscribe to

        Returns:
            The total number of subscribed channels for this client
        """
        self._subscribed_channels.add(channel)
        if channel not in _channels:
            _channels[channel] = set()
        _channels[channel].add(self)
        return self.channel_count

    def unsubscribe(self, channel: str) -> int:
        """
        Unsubscribe from a channel.

        Args:
            channel: The channel name to unsubscribe from

        Returns:
            The total number of subscribed channels remaining for this client
        """
        if channel in self._subscribed_channels:
            self._subscribed_channels.remove(channel)
            if channel in _channels:
                _channels[channel].discard(self)
                if not _channels[channel]:
                    del _channels[channel]
        return self.channel_count


# Global registries
# Key: connection identifier (e.g., peername tuple)
_pubsub_contexts: dict[Any, PubSubContext] = {}

# Key: channel name, Value: set of PubSubContexts currently subscribed
_channels: dict[str, set[PubSubContext]] = {}


def get_pubsub_context(connection_id: Any) -> PubSubContext:
    """
    Get or create a Pub/Sub context for a connection.

    Args:
        connection_id: Unique identifier for the connection

    Returns:
        PubSubContext for this connection
    """
    if connection_id not in _pubsub_contexts:
        _pubsub_contexts[connection_id] = PubSubContext()
    return _pubsub_contexts[connection_id]


def get_subscriber_count(channel: str) -> int:
    """
    Get the number of active clients subscribed to a given channel.

    Args:
        channel: The channel name to query

    Returns:
        The number of connections currently subscribed to the channel
    """
    return len(_channels.get(channel, set()))


async def publish_message(channel: str, message: str) -> int:
    """
    Publish a message to all clients subscribed to a channel.

    Args:
        channel: The target channel.
        message: The message string to deliver.

    Returns:
        The number of clients that successfully received the message.
    """
    # Craft the standard Array format: ["message", channel, message]
    response_payload = ["message", channel, message]
    response_bytes = RESPEncoder.encode(response_payload)

    delivery_count = 0
    subscribers = _channels.get(channel, set())

    for ctx in list(subscribers):  # Copy list to safely iterate while it might change
        if ctx.writer is not None:
            try:
                # writer.write is synchronous, writer.drain is async
                ctx.writer.write(response_bytes)
                await ctx.writer.drain()
                delivery_count += 1
            except Exception as e:
                logger.error(f"Failed to publish to subscriber on channel '{channel}': {e}")
                # Optional: Force unsubscribe if connection is totally broken
                # ctx.unsubscribe(channel)

    return delivery_count


def remove_pubsub_context(connection_id: Any) -> None:
    """
    Remove Pub/Sub context when connection closes.

    Args:
        connection_id: Unique identifier for the connection
    """
    if connection_id in _pubsub_contexts:
        ctx = _pubsub_contexts[connection_id]
        # Clean up subscriptions from the global channels map
        for channel in list(ctx.subscribed_channels):
            ctx.unsubscribe(channel)
        del _pubsub_contexts[connection_id]

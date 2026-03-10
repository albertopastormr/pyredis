"""Pub/Sub state management for Redis clients."""

from typing import Any


class PubSubContext:
    """
    Manages Pub/Sub state for a single connection.

    Tracks the channels a client is subscribed to.
    """

    def __init__(self):
        """Initialize Pub/Sub context."""
        self._subscribed_channels: set[str] = set()

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
        return self.channel_count


# Global registry of Pub/Sub contexts per connection
# Key: connection identifier (e.g., peername tuple)
_pubsub_contexts: dict[Any, PubSubContext] = {}


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


def remove_pubsub_context(connection_id: Any) -> None:
    """
    Remove Pub/Sub context when connection closes.

    Args:
        connection_id: Unique identifier for the connection
    """
    if connection_id in _pubsub_contexts:
        del _pubsub_contexts[connection_id]

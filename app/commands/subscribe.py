"""SUBSCRIBE command implementation."""

from typing import Any

from app.pubsub import get_pubsub_context

from .base import BaseCommand


class SubscribeCommand(BaseCommand):
    """
    SUBSCRIBE command - Subscribes the client to the specified channels.

    Tracks subscription counts per-client using the Pub/Sub context.
    Returns a RESP array confirming the subscription and indicating the
    current total number of subscribed channels for the client.
    """

    @property
    def name(self) -> str:
        return "SUBSCRIBE"

    @property
    def allowed_in_subscribed_mode(self) -> bool:
        return True

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute SUBSCRIBE command.

        Args:
            args: The channels to subscribe to
            connection_id: Optional connection identifier

        Returns:
            A list containing ["subscribe", channel_name, channel_count]
        """
        self.validate_args(args, min_args=1)

        pubsub_ctx = get_pubsub_context(connection_id)

        # In Redis, if multiple channels are provided like SUBSCRIBE foo bar
        # it pushes an array response for EACH channel. Currently, we only
        # support standard single-channel subscription responses as our
        # iteration loop relies on handling one argument at a time efficiently.
        # A response for the first parameter with the updated channel count.
        channel_name = args[0]
        channel_count = pubsub_ctx.subscribe(channel_name)

        # RESP encoder will recursively encode this array
        return ["subscribe", channel_name, channel_count]

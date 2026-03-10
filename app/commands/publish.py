"""PUBLISH command implementation."""

from typing import Any

from app.pubsub import publish_message

from .base import BaseCommand


class PublishCommand(BaseCommand):
    """
    PUBLISH channel message

    Delivers a message to all clients subscribed to the channel.
    Currently only returns the number of active subscribers.
    """

    @property
    def name(self) -> str:
        return "PUBLISH"

    @property
    def is_write_command(self) -> bool:
        """Publish modifies state conceptually for subscribers, often treated as write."""
        # For simple implementations tests it usually doesn't matter strictly,
        # but standard Redis replicates PUBLISH. Let's return True.
        return True

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute PUBLISH command.

        Args:
            args: Command arguments [channel, message]
            connection_id: Unused here.

        Returns:
            The number of clients that received the message.
        """
        self.validate_args(args, min_args=2, max_args=2)
        channel = args[0]
        message = args[1]

        # Evaluate and return subscriber count
        count = await publish_message(channel, message)
        return count

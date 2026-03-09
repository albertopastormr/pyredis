"""SUBSCRIBE command implementation."""

from typing import Any

from .base import BaseCommand


class SubscribeCommand(BaseCommand):
    """
    SUBSCRIBE command - Subscribes the client to the specified channels.

    For Stage 1, it simply returns a confirmation for the single specified channel.
    """

    @property
    def name(self) -> str:
        return "SUBSCRIBE"

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

        channel_name = args[0]
        # RESP encoder will recursively encode this array
        return ["subscribe", channel_name, 1]

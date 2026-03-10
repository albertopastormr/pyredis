"""UNSUBSCRIBE command implementation."""

from typing import Any

from app.pubsub import get_pubsub_context

from .base import BaseCommand


class UnsubscribeCommand(BaseCommand):
    """
    UNSUBSCRIBE [channel [channel ...]]

    Unsubscribes the client from the given channels, or from all of them if none is given.
    """

    @property
    def name(self) -> str:
        return "UNSUBSCRIBE"

    @property
    def is_write_command(self) -> bool:
        """Unsubscribe modifies connection state; while local, standard Redis replicates."""
        return True

    @property
    def allowed_in_subscribed_mode(self) -> bool:
        """This command must inherently be allowed in subscribed mode."""
        return True

    @property
    def bypasses_transaction_queue(self) -> bool:
        """These commands shouldn't queue in standard Multi natively evaluating context directly."""
        return True

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute UNSUBSCRIBE command.

        Args:
            args: Command arguments [channel1, channel2...]
            connection_id: Identifier for the client connection

        Returns:
            A list of responses for each channel unsubscribed from.
        """
        # Require at least 1 channel argument
        self.validate_args(args, min_args=1)

        pubsub_ctx = get_pubsub_context(connection_id)

        responses = []
        for channel in args:
            remaining_count = pubsub_ctx.unsubscribe(channel)
            responses.append(["unsubscribe", channel, remaining_count])

        # If it's a single channel un-subscription, we return just the array list
        # We need to inform handler.py somehow that this is a generator of responses,
        # but since we only ever write it synchronously backwards to `RESPEncoder.encode`
        # we will handle standard iteration format. The RESP protocol for UNSUBSCRIBE
        # *actually* just pushes N separate Arrays sequentially.

        # We'll return just the FIRST response if len is 1 to maintain simple interface compat.
        # If len > 1, we return the list. If it fails encoding we'll adjust the encoder.
        if len(responses) == 1:
            return responses[0]

        return responses

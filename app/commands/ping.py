"""PING command implementation."""

from typing import Any

from app.pubsub import get_pubsub_context

from .base import BaseCommand


class PingCommand(BaseCommand):
    """
    PING command - Tests server connectivity.

    Returns PONG if no argument is provided, otherwise returns the argument.
    """

    @property
    def name(self) -> str:
        return "PING"

    @property
    def allowed_in_subscribed_mode(self) -> bool:
        return True

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute PING command.

        If in subscribed mode, returns a RESP array ["pong", ""] (or with msg).
        Otherwise returns simple string PONG or bulk string of argument.

        Args:
            args: Optional message to echo back
            connection_id: Connection identifier to check subscription state

        Returns:
            'PONG' if no args, otherwise the first argument
        """
        self.validate_args(args, min_args=0, max_args=1)

        # Handle Subscribed Mode Logic
        if connection_id is not None:
            pubsub_ctx = get_pubsub_context(connection_id)
            if pubsub_ctx.is_in_subscribed_mode:
                msg = args[0] if args else ""
                return ["pong", msg]

        # Standard Logic
        if args:
            # PING with message returns the message (bulk string natively handled)
            return args[0]
        else:
            # PING without message returns simple string PONG
            return {"ok": "PONG"}

"""DISCARD command implementation."""

from typing import Any, Optional

from app.transaction import get_transaction_context

from .base import BaseCommand


class DiscardCommand(BaseCommand):
    """
    DISCARD command - Discard all commands in a transaction block.

    Syntax: DISCARD

    Flushes all previously queued commands in a transaction and restores
    the connection to normal state.
    Time complexity: O(1)
    """

    @property
    def name(self) -> str:
        return "DISCARD"

    @property
    def bypasses_transaction_queue(self) -> bool:
        """DISCARD is a transaction control command and always executes."""
        return True

    async def execute(self, args: list[str], connection_id: Optional[Any] = None) -> Any:
        """
        Execute DISCARD command.

        Args:
            args: Should be empty for DISCARD
            connection_id: Connection identifier for transaction tracking

        Returns:
            {'ok': 'OK'} to indicate transaction was discarded
        """
        self.validate_args(args, min_args=0, max_args=0)

        if connection_id is None:
            raise ValueError("ERR DISCARD without MULTI")

        transaction_ctx = get_transaction_context(connection_id)

        if not transaction_ctx.in_transaction:
            raise ValueError("ERR DISCARD without MULTI")

        transaction_ctx.discard_transaction()

        return {"ok": "OK"}

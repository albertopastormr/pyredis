"""MULTI command implementation."""

from typing import Any, Optional

from app.transaction import get_transaction_context

from .base import BaseCommand


class MultiCommand(BaseCommand):
    """
    MULTI command - Mark the start of a transaction block.

    Syntax: MULTI

    Subsequent commands will be queued for atomic execution using EXEC.
    Time complexity: O(1)
    """

    @property
    def name(self) -> str:
        return "MULTI"

    @property
    def bypasses_transaction_queue(self) -> bool:
        """MULTI is a transaction control command and always executes."""
        return True

    async def execute(self, args: list[str], connection_id: Optional[Any] = None) -> Any:
        """
        Execute MULTI command.

        Args:
            args: Should be empty for MULTI
            connection_id: Connection identifier for transaction tracking

        Returns:
            {'ok': 'OK'} to indicate transaction started
        """
        self.validate_args(args, min_args=0, max_args=0)

        if connection_id is not None:
            transaction_ctx = get_transaction_context(connection_id)
            transaction_ctx.start_transaction()

        return {"ok": "OK"}

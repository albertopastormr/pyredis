"""EXEC command implementation."""

from typing import Any, Optional

from app.transaction import get_transaction_context

from .base import BaseCommand


class ExecCommand(BaseCommand):
    """
    EXEC command - Execute all commands in a transaction block.

    Syntax: EXEC

    Executes all previously queued commands in a transaction and restores
    the connection to normal state.
    Time complexity: Depends on commands in the transaction
    """

    @property
    def name(self) -> str:
        return "EXEC"

    @property
    def bypasses_transaction_queue(self) -> bool:
        """EXEC is a transaction control command and always executes."""
        return True

    async def execute(self, args: list[str], connection_id: Optional[Any] = None) -> Any:
        """
        Execute EXEC command.

        Args:
            args: Should be empty for EXEC
            connection_id: Connection identifier for transaction tracking

        Returns:
            List of results from executing all queued commands
        """
        self.validate_args(args, min_args=0, max_args=0)

        if connection_id is None:
            raise ValueError("ERR EXEC without MULTI")

        transaction_ctx = get_transaction_context(connection_id)

        if not transaction_ctx.in_transaction:
            raise ValueError("ERR EXEC without MULTI")

        queued_commands = transaction_ctx.get_queued_commands()

        transaction_ctx.clear_transaction()

        from app.commands import CommandRegistry

        results = []
        for command_name, command_args in queued_commands:
            command_class = CommandRegistry._commands.get(command_name.upper())
            if command_class:
                command_obj = command_class()
                try:
                    result = await command_obj.execute(command_args, connection_id=connection_id)
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e)})
            else:
                results.append({"error": f"ERR unknown command '{command_name}'"})

        return results

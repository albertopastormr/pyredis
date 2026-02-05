"""Base command interface."""

from abc import ABC, abstractmethod
from typing import Any


class BaseCommand(ABC):
    """Abstract base class for all Redis commands."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the command name (e.g., 'PING', 'GET')."""
        pass

    @property
    def bypasses_transaction_queue(self) -> bool:
        """
        Whether this command bypasses transaction queuing.
        
        Transaction control commands (MULTI, EXEC, DISCARD) should return True.
        All other commands should return False (default).
        
        Returns:
            True if command should execute even when in a transaction,
            False if command should be queued when in a transaction.
        """
        return False
    
    @property
    def is_write_command(self) -> bool:
        """
        Indicates if this command modifies data and should be propagated to replicas.
        
        Write commands (SET, DEL, RPUSH, etc.) should return True.
        Read commands (GET, PING, ECHO, etc.) should return False.
        """
        return False

    @abstractmethod
    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute the command asynchronously.

        For synchronous commands, just implement without await.
        For truly async commands (like BLPOP), use await.

        Args:
            args: Command arguments (not including command name)
            connection_id: Optional connection identifier for transaction tracking

        Returns:
            Command result
        """
        pass

    def validate_args(self, args: list[str], min_args: int = None, max_args: int = None) -> None:
        """
        Validate argument count.

        Args:
            args: Command arguments
            min_args: Minimum required arguments
            max_args: Maximum allowed arguments

        Raises:
            ValueError: If argument count is invalid
        """
        if min_args is not None and len(args) < min_args:
            raise ValueError(f"ERR wrong number of arguments for '{self.name}' command")

        if max_args is not None and len(args) > max_args:
            raise ValueError(f"ERR wrong number of arguments for '{self.name}' command")

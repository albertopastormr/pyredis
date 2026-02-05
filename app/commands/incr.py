"""INCR command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class IncrCommand(BaseCommand):
    """
    INCR command - Increment the integer value of a key by one.

    Syntax: INCR key

    Increments the number stored at key by one. If the key does not exist,
    it is set to 0 before performing the operation.
    Time complexity: O(1)
    """

    @property
    def name(self) -> str:
        return "INCR"
    
    @property
    def is_write_command(self) -> bool:
        """INCR modifies data and must be propagated to replicas."""
        return True

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute INCR command.

        Args:
            args: [key]

        Returns:
            The new value after incrementing

        Raises:
            ValueError: If the key contains a value that cannot be represented as integer
        """
        self.validate_args(args, min_args=1, max_args=1)

        key = args[0]

        try:
            storage = get_storage()
            new_value = storage.incr(key)
            return new_value
        except Exception as e:
            raise ValueError(f"ERR {str(e)}") from e

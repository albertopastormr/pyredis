"""RPUSH command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class RpushCommand(BaseCommand):
    """
    RPUSH command - Append values to a list.

    Syntax: RPUSH key value [value ...]
    Creates list if it doesn't exist.
    Returns: Integer - length of list after push
    Time complexity: O(N) where N is number of values
    """

    @property
    def name(self) -> str:
        return "RPUSH"
    
    @property
    def is_write_command(self) -> bool:
        """RPUSH modifies data and must be propagated to replicas."""
        return True

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute RPUSH command.

        Args:
            args: [key, value, ...] at least 2 arguments

        Returns:
            Integer - length of list after push
        """
        self.validate_args(args, min_args=2)

        key = args[0]
        values = args[1:]

        storage = get_storage()
        length = storage.rpush(key, *values)

        return length

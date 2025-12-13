"""LPUSH command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class LpushCommand(BaseCommand):
    """
    LPUSH command - Prepend values to a list.

    Syntax: LPUSH key value [value ...]
    Creates list if it doesn't exist.
    Returns: Integer - length of list after push
    Time complexity: O(N) where N is number of values
    """

    @property
    def name(self) -> str:
        return "LPUSH"

    async def execute(self, args: list[str]) -> Any:
        """
        Execute LPUSH command.

        Args:
            args: [key, value, ...] at least 2 arguments

        Returns:
            Integer - length of list after push
        """
        self.validate_args(args, min_args=2)

        key = args[0]
        values = args[1:]

        storage = get_storage()
        length = storage.lpush(key, *values)

        return length

"""LRANGE command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class LrangeCommand(BaseCommand):
    """
    LRANGE command - Get range of elements from a list.

    Syntax: LRANGE key start stop
    Returns: Array of elements in the specified range

    Rules:
    - If list doesn't exist, returns empty list
    - If stop > length, treats as length (returns till end)
    - If start > stop or start > length, returns empty list
    """

    @property
    def name(self) -> str:
        return "LRANGE"

    async def execute(self, args: list[str]) -> Any:
        """
        Execute LRANGE command.

        Args:
            args: [key, start, stop]

        Returns:
            List of elements in range
        """
        self.validate_args(args, min_args=3, max_args=3)

        key = args[0]

        try:
            start = int(args[1])
            stop = int(args[2])
        except ValueError as ex:
            raise ValueError("ERR value is not an integer or out of range") from ex

        storage = get_storage()
        result = storage.lrange(key, start, stop)

        return result

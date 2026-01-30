"""LLEN command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class LlenCommand(BaseCommand):
    """
    LLEN command - Get length of a list.

    Syntax: LLEN key
    Returns: Integer - length of list

    Rules:
    - If list doesn't exist, returns 0
    """

    @property
    def name(self) -> str:
        return "LLEN"

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute LLEN command.

        Args:
            args: [key]

        Returns:
            Integer - length of list
        """
        self.validate_args(args, min_args=1, max_args=1)

        key = args[0]

        storage = get_storage()
        result = storage.llen(key)

        return result

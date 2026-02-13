"""LPOP command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class LpopCommand(BaseCommand):
    """
    LPOP command - Remove and return elements from the left of a list.

    Syntax: LPOP key [count]
    If count is provided, removes that many elements.
    If count > length, removes all elements.
    Returns: Single element (if no count) or array of elements
    Time complexity: O(N) where N is count
    """

    @property
    def name(self) -> str:
        return "LPOP"

    @property
    def is_write_command(self) -> bool:
        """LPOP modifies data and must be propagated to replicas."""
        return True

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute LPOP command.

        Args:
            args: [key] or [key, count]

        Returns:
            Single element string (count=1) or list of elements, None if key doesn't exist
        """
        self.validate_args(args, min_args=1, max_args=2)

        key = args[0]
        count = 1  # Default count

        # Parse count if provided
        if len(args) == 2:
            try:
                count = int(args[1])
                if count < 0:
                    raise ValueError("ERR value is out of range, must be positive")
            except ValueError as ex:
                if "out of range" in str(ex):
                    raise
                raise ValueError("ERR value is not an integer or out of range") from ex

        storage = get_storage()
        result = storage.lpop(key, count)

        if result is None:
            return None

        if len(args) == 1:
            return result[0] if result else None

        return result

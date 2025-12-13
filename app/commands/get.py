"""GET command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class GetCommand(BaseCommand):
    """
    GET command - Get the value of a key.

    Syntax: GET key

    Returns the value of key, or nil if key doesn't exist.
    Time complexity: O(1)
    """

    @property
    def name(self) -> str:
        return "GET"

    async def execute(self, args: list[str]) -> Any:
        """
        Execute GET command.

        Args:
            args: [key]

        Returns:
            Value if key exists, None if key doesn't exist
        """
        self.validate_args(args, min_args=1, max_args=1)

        key = args[0]

        try:
            storage = get_storage()
            value = storage.get(key)
            return value
        except Exception as e:
            raise ValueError(f"ERR {str(e)}") from e

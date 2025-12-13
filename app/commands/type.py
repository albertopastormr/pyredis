"""TYPE command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class TypeCommand(BaseCommand):
    """
    TYPE command - Returns the type of a key.

    Syntax: TYPE key

    Returns:
        "string" - for string values
        "list" - for list values
        "none" - if key doesn't exist

    Time complexity: O(1)
    """

    @property
    def name(self) -> str:
        return "TYPE"

    async def execute(self, args: list[str]) -> Any:
        """
        Execute TYPE command.

        Args:
            args: [key]

        Returns:
            Simple string representing the type: "string", "list", or "none"
        """
        self.validate_args(args, min_args=1, max_args=1)

        key = args[0]
        storage = get_storage()

        # Get the type from storage
        key_type = storage.type(key)

        # Return as simple string (RESP format: +string\r\n)
        return {"ok": key_type}

"""XRANGE command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class XrangeCommand(BaseCommand):
    """
    XRANGE command - Retrieve entries from a stream within ID range.

    Syntax: XRANGE key start end
    Returns: Array of arrays, each containing [id, [field, value, ...]]
    Time complexity: O(N) where N is number of entries in range
    """

    @property
    def name(self) -> str:
        return "XRANGE"

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute XRANGE command.

        Args:
            args: [key, start_id, end_id]

        Returns:
            List of [entry_id, [field1, value1, field2, value2, ...]]
        """
        self.validate_args(args, min_args=3, max_args=3)

        key = args[0]
        start_id = args[1]
        end_id = args[2]

        storage = get_storage()
        entries = storage.xrange(key, start_id, end_id)

        # Format output as array of arrays
        # Each entry: [id, [field1, value1, field2, value2, ...]]
        result = []
        for entry_id, fields in entries:
            # Flatten fields dict into array: [k1, v1, k2, v2, ...]
            fields_array = []
            for field_name, field_value in fields.items():
                fields_array.append(field_name)
                fields_array.append(field_value)

            result.append([entry_id, fields_array])

        return result

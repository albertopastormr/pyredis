"""XADD command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class XaddCommand(BaseCommand):
    """
    XADD command - Append an entry to a stream.

    Syntax: XADD key ID field value [field value ...]
    Creates stream if it doesn't exist.
    Returns: Bulk string - the entry ID
    Time complexity: O(1)
    """

    @property
    def name(self) -> str:
        return "XADD"

    async def execute(self, args: list[str]) -> Any:
        """
        Execute XADD command.

        Args:
            args: [key, entry_id, field1, value1, field2, value2, ...]
                  Minimum 4 arguments (key + ID + 1 field-value pair)

        Returns:
            Bulk string - the entry ID that was added

        Raises:
            ValueError: If wrong number of arguments or odd field-value pairs
        """
        # Minimum: key, ID, and at least one field-value pair (4 args)
        self.validate_args(args, min_args=4)

        key = args[0]
        entry_id = args[1]
        field_value_args = args[2:]

        # Must have even number of field-value pairs
        if len(field_value_args) % 2 != 0:
            raise ValueError(f"ERR wrong number of arguments for '{self.name}' command")

        # Parse field-value pairs into dict
        fields = {}
        for i in range(0, len(field_value_args), 2):
            field_name = field_value_args[i]
            field_value = field_value_args[i + 1]
            fields[field_name] = field_value

        storage = get_storage()
        result_id = storage.xadd(key, entry_id, fields)

        return result_id

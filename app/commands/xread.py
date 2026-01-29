"""XREAD command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class XreadCommand(BaseCommand):
    """
    XREAD command - Read entries from streams after specified IDs.

    Syntax: XREAD STREAMS key1 key2 ... id1 id2 ...
    Returns: Array of [stream_key, [[id, [field, value, ...]], ...]] for each stream
    Time complexity: O(N) where N is total entries returned
    """

    @property
    def name(self) -> str:
        return "XREAD"

    async def execute(self, args: list[str]) -> Any:
        """
        Execute XREAD command.

        Args:
            args: [STREAMS, key1, key2, ..., id1, id2, ...]

        Returns:
            List of [stream_key, [[entry_id, [field1, value1, ...]], ...]]
            for each stream with entries. Returns None if no entries found.
        """
        # Need at least 1 arg (STREAMS keyword)
        if len(args) == 0:
            raise ValueError(f"ERR wrong number of arguments for '{self.name}' command")

        # Find STREAMS keyword (case-insensitive)
        if args[0].upper() != "STREAMS":
            raise ValueError(f"ERR syntax error")

        # После STREAMS нужно минимум 2 аргумента (key + id)
        if len(args) < 3:
            raise ValueError(f"ERR wrong number of arguments for '{self.name}' command")

        # Everything after STREAMS is keys and IDs
        keys_and_ids = args[1:]

        if len(keys_and_ids) % 2 != 0:
            raise ValueError(f"ERR Unbalanced 'xread' list of streams: for each stream key an ID must be specified.")

        mid = len(keys_and_ids) // 2
        keys = keys_and_ids[:mid]
        ids = keys_and_ids[mid:]

        streams = list(zip(keys, ids))

        storage = get_storage()
        results = storage.xread(streams)

        if not results:
            return None

        # Format output as array of [stream_key, entries]
        # Each entry: [id, [field1, value1, field2, value2, ...]]
        formatted = []
        for stream_key, entries in results:
            formatted_entries = []
            for entry_id, fields in entries:
                # Flatten fields dict into array: [k1, v1, k2, v2, ...]
                fields_array = []
                for field_name, field_value in fields.items():
                    fields_array.append(field_name)
                    fields_array.append(field_value)
                formatted_entries.append([entry_id, fields_array])
            formatted.append([stream_key, formatted_entries])

        return formatted

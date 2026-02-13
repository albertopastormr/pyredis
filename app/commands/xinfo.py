"""XINFO command implementation."""

from typing import Any

from app.storage import get_storage

from .base import BaseCommand


class XinfoCommand(BaseCommand):
    """
    XINFO command - Get stream information.

    Syntax: XINFO [Start of command] STREAM <key>
    Currently only supports STREAM subcommand.
    Returns: List of metadata about the stream.
    Time complexity: O(1)
    """

    @property
    def name(self) -> str:
        return "XINFO"

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute XINFO command.

        Args:
            args: [STREAM, key]

        Returns:
            List of field-value pairs with stream info.

        Raises:
            ValueError: If wrong number of arguments or unknown subcommand
        """
        self.validate_args(args, min_args=2)

        subcommand = args[0].upper()
        if subcommand != "STREAM":
            # Real Redis might accept other subcommands (GROUPS, CONSUMERS)
            # but for now we focus on STREAM or raise error
            raise ValueError(f"ERR unknown subcommand '{subcommand}'")

        key = args[1]
        storage = get_storage()

        # Check existence/type by trying to get info
        # Storage.xinfo raises WrongTypeError if key is not a stream
        info = storage.xinfo(key)

        if info is None:
            raise ValueError("ERR no such key")

        # Format as flat list: [key1, val1, key2, val2, ...]
        result = []

        # Add basic fields
        result.extend(["length", info.get("length", 0)])
        result.extend(["last-generated-id", info.get("last-generated-id", "0-0")])

        # Add entries (must handle None if empty)
        first = info.get("first-entry")
        if first:
            # Format entry: [id, [k, v, ...]]
            entry_id, fields = first
            fields_array = []
            for k, v in fields.items():
                fields_array.append(k)
                fields_array.append(v)
            result.extend(["first-entry", [entry_id, fields_array]])
        else:
            result.extend(["first-entry", None])

        last = info.get("last-entry")
        if last:
            entry_id, fields = last
            fields_array = []
            for k, v in fields.items():
                fields_array.append(k)
                fields_array.append(v)
            result.extend(["last-entry", [entry_id, fields_array]])
        else:
            result.extend(["last-entry", None])

        return result

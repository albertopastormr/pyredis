"""XREAD command implementation."""

import asyncio
from typing import Any, Optional

from app.blocking import register_waiter, unregister_waiter
from app.storage import get_storage

from .base import BaseCommand


class XreadCommand(BaseCommand):
    """
    XREAD command - Read entries from streams after specified IDs.

    Syntax: XREAD [BLOCK milliseconds] STREAMS key1 key2 ... id1 id2 ...
    Returns: Array of [stream_key, [[id, [field, value, ...]], ...]] for each stream
    Time complexity: O(N) where N is total entries returned
    """

    @property
    def name(self) -> str:
        return "XREAD"

    def _parse_args(self, args: list[str]) -> tuple[Optional[float], list[tuple[str, str]]]:
        """
        Parse XREAD arguments.

        Returns:
            Tuple of (block_timeout_seconds or None, list of (key, id) tuples)
        """
        if len(args) == 0:
            raise ValueError(f"ERR wrong number of arguments for '{self.name}' command")

        block_timeout: Optional[float] = None
        idx = 0

        # Check for BLOCK option
        if args[idx].upper() == "BLOCK":
            if len(args) < 2:
                raise ValueError(f"ERR wrong number of arguments for '{self.name}' command")
            try:
                block_ms = int(args[1])
                if block_ms < 0:
                    raise ValueError("ERR timeout is negative")
                # Convert to seconds; 0 means wait indefinitely
                block_timeout = block_ms / 1000.0 if block_ms > 0 else 0
            except ValueError as e:
                if "negative" in str(e):
                    raise
                raise ValueError("ERR timeout is not an integer or out of range")
            idx = 2

        # Expect STREAMS keyword
        if idx >= len(args):
            raise ValueError(f"ERR wrong number of arguments for '{self.name}' command")

        if args[idx].upper() != "STREAMS":
            raise ValueError("ERR syntax error")

        idx += 1

        # Everything after STREAMS is keys and IDs
        keys_and_ids = args[idx:]

        if len(keys_and_ids) == 0:
            raise ValueError(f"ERR wrong number of arguments for '{self.name}' command")

        if len(keys_and_ids) % 2 != 0:
            raise ValueError("ERR Unbalanced 'xread' list of streams: for each stream key an ID must be specified.")

        mid = len(keys_and_ids) // 2
        keys = keys_and_ids[:mid]
        ids = keys_and_ids[mid:]

        streams = list(zip(keys, ids))
        return block_timeout, streams

    def _query_streams(self, streams: list[tuple[str, str]]) -> Optional[list]:
        """Query streams and format results."""
        storage = get_storage()
        results = storage.xread(streams)

        if not results:
            return None

        # Format output as array of [stream_key, entries]
        formatted = []
        for stream_key, entries in results:
            formatted_entries = []
            for entry_id, fields in entries:
                fields_array = []
                for field_name, field_value in fields.items():
                    fields_array.append(field_name)
                    fields_array.append(field_value)
                formatted_entries.append([entry_id, fields_array])
            formatted.append([stream_key, formatted_entries])

        return formatted

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute XREAD command.

        Args:
            args: [BLOCK ms] STREAMS key1 key2 ... id1 id2 ...

        Returns:
            List of [stream_key, [[entry_id, [field1, value1, ...]], ...]]
            for each stream with entries. Returns None/null_array if no entries.
        """
        block_timeout, streams = self._parse_args(args)

        # Resolve '$' IDs using XINFO
        resolved_streams = []
        storage = get_storage()
        
        for key, start_id in streams:
            if start_id == "$":
                # Get last generated ID from XINFO
                # If key doesn't exist or is empty, use 0-0
                try:
                    info = storage.xinfo(key)
                    if info:
                        resolved_id = info["last-generated-id"]
                    else:
                        resolved_id = "0-0"
                except Exception:
                    # On error (e.g. wrong type), keep "$" (storage.xread will likely fail or return nothing)
                    # Ideally we should fail early if wrong type, but storage.xread handles it
                     resolved_id = "$" 
                resolved_streams.append((key, resolved_id))
            else:
                resolved_streams.append((key, start_id))

        # Use resolved streams for queries
        streams = resolved_streams

        # Try immediate read
        result = self._query_streams(streams)
        if result is not None:
            return result

        # If not blocking, return None immediately
        if block_timeout is None:
            return None

        # Blocking mode: wait for data
        keys = [key for key, _ in streams]
        events = []

        # Register waiters for all keys
        for key in keys:
            event = asyncio.Event()
            register_waiter(key, event)
            events.append((key, event))

        try:
            # Wait for any event to be set
            wait_tasks = [event.wait() for _, event in events]

            if block_timeout > 0:
                # Wait with timeout
                try:
                    done, pending = await asyncio.wait(
                        [asyncio.create_task(t) for t in wait_tasks],
                        timeout=block_timeout,
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    # Cancel pending tasks
                    for task in pending:
                        task.cancel()
                except asyncio.TimeoutError:
                    return {"null_array": True}

                if not done:
                    # Timeout with no data
                    return {"null_array": True}
            else:
                # Wait indefinitely for first event
                await asyncio.wait(
                    [asyncio.create_task(t) for t in wait_tasks],
                    return_when=asyncio.FIRST_COMPLETED
                )

            # Re-query streams after notification
            result = self._query_streams(streams)
            return result if result is not None else {"null_array": True}

        finally:
            # Unregister all waiters
            for key, event in events:
                unregister_waiter(key, event)

"""Redis value types and type checking."""

import time
from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
from typing import Optional

from app.exceptions import WrongTypeError


# Stream ID constants
MIN_STREAM_MS = 0
MIN_STREAM_SEQ = 0
MAX_STREAM_MS = 2**63 - 1
MAX_STREAM_SEQ = 2**63 - 1


class RedisType(Enum):
    """Enum for Redis data types."""

    STRING = "string"
    LIST = "list"
    SET = "set"
    HASH = "hash"
    STREAM = "stream"


def raise_wrong_type() -> None:
    """Raise a consistent WRONGTYPE error."""
    raise WrongTypeError()


class RedisValue(ABC):
    """Base class for all Redis value types."""

    @abstractmethod
    def get_type(self) -> RedisType:
        """Return type enum."""
        pass


class RedisString(RedisValue):
    """Redis string type."""

    def __init__(self, value: str):
        self.value = value

    def get_type(self) -> RedisType:
        return RedisType.STRING

    def __repr__(self) -> str:
        return f"RedisString({self.value!r})"


class RedisList(RedisValue):
    """Redis list type."""

    def __init__(self, values: Optional[list[str]] = None):
        self.values = values or []

    def get_type(self) -> RedisType:
        return RedisType.LIST

    def rpush(self, *items: str) -> int:
        """Append items and return new length."""
        self.values.extend(items)
        return len(self.values)

    def lpush(self, *items: str) -> int:
        """Prepend items and return new length."""
        items = list(items)
        items.reverse()  # Reverse order to maintain original order
        self.values = items + self.values
        return len(self.values)

    def lpop(self, count: int = 1) -> list:
        """
        Remove and return elements from the left.

        Args:
            count: Number of elements to pop (default 1)

        Returns:
            List of popped elements, or empty list if count is 0
        """
        if count <= 0:
            return []

        if count >= len(self.values):
            result = self.values[:]
            self.values = []
            return result

        result = self.values[:count]
        self.values = self.values[count:]
        return result

    def lrange(self, start: int, stop: int) -> list[str]:
        """
        Get range of elements.

        Rules:
        - Negative indices count from end (-1 = last, -2 = second-to-last)
        - If start > length, return empty list
        - If stop > length, treat as length
        - If start > stop (after conversion), return empty list
        - Both indices are inclusive
        """
        length = len(self.values)

        if length == 0:
            return []

        if start < 0:
            start = length + start
            if start < 0:
                start = 0

        if stop < 0:
            stop = length + stop
            if stop < 0:
                stop = 0

        if start >= length:
            return []

        if stop < start:
            return []

        if stop >= length:
            stop = length - 1

        return self.values[start : stop + 1]

    def length(self) -> int:
        """Get list length for LLEN command."""
        return len(self.values)

    def __len__(self) -> int:
        """Support len() built-in."""
        return len(self.values)

    def __repr__(self) -> str:
        return f"RedisList({self.values!r})"


class StreamEntry:
    """Redis stream entry - ID with key-value pairs."""

    def __init__(self, entry_id: str, fields: dict[str, str]):
        self.id = entry_id
        self.fields = fields

    def __repr__(self) -> str:
        return f"StreamEntry(id={self.id!r}, fields={self.fields!r})"


class RedisStream(RedisValue):
    """Redis stream type."""

    def __init__(self):
        self.entries: list[StreamEntry] = []

    def get_type(self) -> RedisType:
        return RedisType.STREAM

    def xrange(self, start_id: str, end_id: str) -> list[StreamEntry]:
        """
        Get entries within ID range (inclusive).

        Args:
            start_id: Start ID (e.g., "1526985054069-0" or "1526985054069")
            end_id: End ID (e.g., "1526985054079-0" or "1526985054079")

        Returns:
            List of StreamEntry objects within the range
        """
        # Parse start and end IDs, handling optional sequence numbers
        start_ms, start_seq = self._parse_range_id(start_id, is_start=True)
        end_ms, end_seq = self._parse_range_id(end_id, is_start=False)

        # Filter entries within range
        result = []
        for entry in self.entries:
            entry_ms, entry_seq = self._parse_entry_id(entry.id)
            
            # Check if entry is within range (inclusive)
            if self._is_in_range(entry_ms, entry_seq, start_ms, start_seq, end_ms, end_seq):
                result.append(entry)

        return result

    def _parse_range_id(self, range_id: str, is_start: bool) -> tuple[int, int]:
        """
        Parse range ID, handling optional sequence number and special markers.

        Args:
            range_id: Range ID (e.g., "123-456", "123", "-", or "+")
            is_start: True if this is the start ID, False if end ID

        Returns:
            Tuple of (milliseconds, sequence_number)
        """
        # Handle special markers
        if range_id == "-":
            # Minimum possible ID
            return (MIN_STREAM_MS, MIN_STREAM_SEQ)
        
        if range_id == "+":
            # Maximum possible ID
            return (MAX_STREAM_MS, MAX_STREAM_SEQ)
        
        if "-" not in range_id:
            # No sequence number provided
            ms_time = int(range_id)
            # Start ID defaults to 0, end ID defaults to max sequence
            seq_num = MIN_STREAM_SEQ if is_start else MAX_STREAM_SEQ
            return ms_time, seq_num
        
        # Has sequence number, parse normally
        return self._parse_entry_id(range_id)

    def _is_in_range(
        self,
        entry_ms: int,
        entry_seq: int,
        start_ms: int,
        start_seq: int,
        end_ms: int,
        end_seq: int,
    ) -> bool:
        """
        Check if entry is within the specified range (inclusive).

        Args:
            entry_ms: Entry milliseconds
            entry_seq: Entry sequence number
            start_ms: Start milliseconds
            start_seq: Start sequence number
            end_ms: End milliseconds
            end_seq: End sequence number

        Returns:
            True if entry is within range
        """
        # Check if entry >= start
        if entry_ms < start_ms:
            return False
        if entry_ms == start_ms and entry_seq < start_seq:
            return False

        # Check if entry <= end
        if entry_ms > end_ms:
            return False
        if entry_ms == end_ms and entry_seq > end_seq:
            return False

        return True

    def xadd(self, entry_id: str, fields: dict[str, str]) -> str:
        """
        Add entry to stream with ID validation or auto-generation.

        Args:
            entry_id: Entry ID (e.g., "1526985054069-0", "1-*", or "*")
            fields: Key-value pairs for the entry

        Returns:
            The entry ID that was added (auto-generated if needed)

        Raises:
            ValueError: If entry ID is invalid or not greater than last entry
        """
        generated_id = self._generate_entry_id(entry_id)
        self._validate_entry_id(generated_id)

        entry = StreamEntry(generated_id, fields)
        self.entries.append(entry)
        return generated_id

    def _generate_entry_id(self, entry_id: str) -> str:
        """
        Generate entry ID if it contains wildcards (*).

        Args:
            entry_id: Entry ID pattern (e.g., "*", "1-*", or "123-456")

        Returns:
            Fully resolved entry ID

        Raises:
            ValueError: If ID format is invalid
        """
        if entry_id == "*":
            # Auto-generate both timestamp and sequence
            # Use time_ns() for precise millisecond timestamp (avoids float rounding)
            ms_time = time.time_ns() // 1_000_000
            seq_num = self._get_next_sequence_number(ms_time)
            return f"{ms_time}-{seq_num}"
        
        if "-" in entry_id:
            parts = entry_id.split("-", 1)
            if len(parts) == 2:
                ms_part, seq_part = parts
                
                if seq_part == "*":
                    try:
                        ms_time = int(ms_part)
                        if ms_time < 0:
                            raise ValueError("ERR Invalid stream ID specified as stream command argument")
                        seq_num = self._get_next_sequence_number(ms_time)
                        return f"{ms_time}-{seq_num}"
                    except ValueError as e:
                        if "Invalid stream ID" in str(e):
                            raise
                        raise ValueError("ERR Invalid stream ID specified as stream command argument")
        
        # Not a wildcard pattern, return as-is
        return entry_id

    def _get_next_sequence_number(self, ms_time: int) -> int:
        """
        Get the next sequence number for a given timestamp.

        Args:
            ms_time: Milliseconds timestamp

        Returns:
            Next sequence number based on stream state
        """
        if not self.entries:
            # Empty stream: use 0 for timestamp > 0, use 1 for timestamp = 0
            return 1 if ms_time == 0 else 0
        
        # Get last entry's timestamp and sequence
        last_entry_id = self.entries[-1].id
        last_ms_time, last_seq_num = self._parse_entry_id(last_entry_id)
        
        if ms_time == last_ms_time:
            # Same timestamp: increment sequence
            return last_seq_num + 1
        else:
            # Different timestamp (new or older)
            # For timestamp 0, always start at 1
            # For other timestamps, start at 0
            return 1 if ms_time == 0 else 0

    def _validate_entry_id(self, entry_id: str) -> None:
        """
        Validate that entry ID is valid and greater than last entry.

        Args:
            entry_id: Entry ID to validate

        Raises:
            ValueError: If entry ID is invalid or not greater than last entry
        """
        # Parse and validate the entry ID format
        ms_time, seq_num = self._parse_entry_id(entry_id)

        # Check for minimum ID (0-0 is never valid)
        if ms_time == 0 and seq_num == 0:
            raise ValueError(
                "ERR The ID specified in XADD must be greater than 0-0"
            )

        # Validate against last entry if stream has entries
        if self.entries:
            last_entry_id = self.entries[-1].id
            last_ms_time, last_seq_num = self._parse_entry_id(last_entry_id)

            # ID must be strictly greater than last entry
            if ms_time < last_ms_time:
                raise ValueError(
                    "ERR The ID specified in XADD is equal or smaller than the "
                    "target stream top item"
                )
            elif ms_time == last_ms_time and seq_num <= last_seq_num:
                raise ValueError(
                    "ERR The ID specified in XADD is equal or smaller than the "
                    "target stream top item"
                )

    def _parse_entry_id(self, entry_id: str) -> tuple[int, int]:
        """
        Parse entry ID into milliseconds and sequence number.

        Args:
            entry_id: Entry ID string (e.g., "1526985054069-0")

        Returns:
            Tuple of (milliseconds_time, sequence_number)

        Raises:
            ValueError: If ID format is invalid
        """
        try:
            parts = entry_id.split("-")
            if len(parts) != 2:
                raise ValueError("ERR Invalid stream ID specified as stream command argument")

            ms_time = int(parts[0])
            seq_num = int(parts[1])

            if ms_time < 0 or seq_num < 0:
                raise ValueError("ERR Invalid stream ID specified as stream command argument")

            return ms_time, seq_num
        except (ValueError, AttributeError) as e:
            if "Invalid stream ID" in str(e):
                raise
            raise ValueError("ERR Invalid stream ID specified as stream command argument")

    def __len__(self) -> int:
        """Support len() built-in."""
        return len(self.entries)

    def __repr__(self) -> str:
        return f"RedisStream(entries={self.entries!r})"


def require_type(expected_type: RedisType):
    """
    Decorator to enforce type checking on storage methods.

    ONLY checks type when key exists
    Each method handles its own missing key logic.

    Args:
        expected_type: Required RedisType (e.g., RedisType.LIST)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, key: str, *args, **kwargs):
            if key in self._data:
                value = self._data[key]
                if value.get_type() != expected_type:
                    raise_wrong_type()

            return func(self, key, *args, **kwargs)

        return wrapper

    return decorator

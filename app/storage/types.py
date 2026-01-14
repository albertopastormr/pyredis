"""Redis value types and type checking."""

from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
from typing import Optional

from app.exceptions import WrongTypeError


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

    def xadd(self, entry_id: str, fields: dict[str, str]) -> str:
        """
        Add entry to stream with ID validation.

        Args:
            entry_id: Entry ID (e.g., "1526985054069-0")
            fields: Key-value pairs for the entry

        Returns:
            The entry ID that was added

        Raises:
            ValueError: If entry ID is invalid or not greater than last entry
        """
        # Validate the entry ID
        self._validate_entry_id(entry_id)

        # Add entry to stream
        entry = StreamEntry(entry_id, fields)
        self.entries.append(entry)
        return entry_id

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

        # Validate against last entry or minimum ID
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
        else:
            # For empty streams, ID must be > "0-0"
            if ms_time == 0 and seq_num == 0:
                raise ValueError(
                    "ERR The ID specified in XADD must be greater than 0-0"
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

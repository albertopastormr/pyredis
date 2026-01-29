"""Base storage interface."""

from abc import ABC, abstractmethod
from typing import Optional


class BaseStorage(ABC):
    """
    Abstract base class for storage backends.

    This allows us to swap storage implementations without changing commands.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """
        Get value by key.

        Args:
            key: The key to look up

        Returns:
            Value if key exists, None otherwise
        """
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        """
        Set key to value.

        Args:
            key: The key to set
            value: The value to store
        """
        pass

    @abstractmethod
    def set_with_ttl(self, key: str, value: str, ttl_ms: int) -> None:
        """
        Set key to value with TTL (Time To Live).

        Args:
            key: The key to set
            value: The value to store
            ttl_ms: Time to live in milliseconds
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a key.

        Args:
            key: The key to delete

        Returns:
            True if key existed, False otherwise
        """
        pass

    @abstractmethod
    def llen(self, key: str) -> int:
        """Get list length. Returns 0 if key doesn't exist."""
        pass

    @abstractmethod
    def lpop(self, key: str, count: int = 1) -> Optional[list[str]]:
        """
        Remove and return elements from the left of the list.

        Args:
            key: The list key
            count: Number of elements to pop (default 1)

        Returns:
            List of popped elements, or None if key doesn't exist
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if key exists.

        Args:
            key: The key to check

        Returns:
            True if key exists, False otherwise
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all data."""
        pass

    @abstractmethod
    def rpush(self, key: str, *values: str) -> int:
        """
        Append values to list.

        Args:
            key: The list key
            values: Values to append

        Returns:
            Length of list after push
        """
        pass

    @abstractmethod
    def lpush(self, key: str, *values: str) -> int:
        """
        Prepend values to list.

        Args:
            key: The list key
            values: Values to prepend

        Returns:
            Length of list after push
        """
        pass

    @abstractmethod
    def lrange(self, key: str, start: int, stop: int) -> list[str]:
        """
        Get list elements in range.

        Args:
            key: The list key
            start: Start index
            stop: Stop index (inclusive)

        Returns:
            List of elements in range
        """
        pass

    @abstractmethod
    def type(self, key: str) -> str:
        """
        Get the type of a key.

        Args:
            key: Key to check

        Returns:
            "string" for string values
            "list" for list values
            "stream" for stream values
            "none" if key doesn't exist
        """
        pass

    @abstractmethod
    def xadd(self, key: str, entry_id: str, fields: dict[str, str]) -> str:
        """
        Add entry to a stream.

        Args:
            key: The stream key
            entry_id: Entry ID (e.g., "1526985054069-0")
            fields: Key-value pairs for the entry

        Returns:
            The entry ID that was added
        """
        pass

    @abstractmethod
    def xrange(self, key: str, start_id: str, end_id: str) -> list[tuple[str, dict[str, str]]]:
        """
        Get entries from a stream within ID range.

        Args:
            key: The stream key
            start_id: Start ID (inclusive)
            end_id: End ID (inclusive)

        Returns:
            List of tuples (entry_id, fields_dict)
        """
        pass

    @abstractmethod
    def xread(
        self, streams: list[tuple[str, str]]
    ) -> list[tuple[str, list[tuple[str, dict[str, str]]]]]:
        """
        Read entries from multiple streams with ID greater than specified (exclusive).

        Args:
            streams: List of (stream_key, start_id) tuples

        Returns:
            List of (stream_key, entries) tuples where entries is list of (entry_id, fields_dict).
            Only includes streams that have entries; empty streams are omitted.
        """
        pass

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

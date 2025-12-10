"""Redis value type system."""

from abc import ABC, abstractmethod
from typing import List, Optional
from enum import Enum
from functools import wraps


class RedisType(Enum):
    """Redis data types."""
    STRING = "string"
    LIST = "list"
    SET = "set"
    HASH = "hash"


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
    
    def __init__(self, values: Optional[List[str]] = None):
        self.values = values or []
    
    def get_type(self) -> RedisType:
        return RedisType.LIST
    
    def rpush(self, *items: str) -> int:
        """Append items and return new length."""
        self.values.extend(items)
        return len(self.values)
    
    def lrange(self, start: int, stop: int) -> List[str]:
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
        if stop < 0:
            stop = length + stop
        
        if start < 0 or start >= length:
            return []
        
        if stop < start:
            return []
        
        if stop >= length:
            stop = length - 1
        
        return self.values[start:stop+1]
    
    def __len__(self) -> int:
        return len(self.values)
    
    def __repr__(self) -> str:
        return f"RedisList({self.values!r})"


def raise_wrong_type():
    """Centralized WRONGTYPE error"""
    raise ValueError("WRONGTYPE Operation against a key holding the wrong kind of value")


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

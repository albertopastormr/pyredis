"""In-memory storage implementation using Python dict."""

import time
from typing import Optional, Dict, List
from .base import BaseStorage
from .types import RedisValue, RedisString, RedisList, RedisType, require_type


class InMemoryStorage(BaseStorage):
    """
    In-memory storage using Python dict.
    
    This is the primary storage mechanism - same as real Redis.
    Thread-safe with asyncio (single-threaded event loop + GIL).
    Supports TTL (Time To Live) for key expiration.
    Supports multiple data types: strings, lists.
    """
    
    def __init__(self):
        """Initialize empty storage."""
        self._data: Dict[str, RedisValue] = {}
        self._expiry: Dict[str, float] = {}  # key -> monotonic expiration time
    
    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired."""
        if key not in self._expiry:
            return False
        return time.monotonic() > self._expiry[key]
    
    @require_type(RedisType.STRING)
    def get(self, key: str) -> Optional[str]:
        """
        Get value by key.
        
        Returns None if key doesn't exist or has expired.
        Time complexity: O(1) average case
        
        Args:
            key: The key to look up
        
        Returns:
            Value if key exists and not expired, None otherwise
        """
        if key not in self._data:
            return None
        
        if self._is_expired(key):
            del self._data[key]
            del self._expiry[key]
            return None
        
        return self._data[key].value
    
    def set(self, key: str, value: str) -> None:
        """
        Set key to value.
        
        Overwrites any existing type.
        Time complexity: O(1) average case
        
        Args:
            key: The key to set
            value: The value to store
        """
        self._data[key] = RedisString(value)
        if key in self._expiry:
            del self._expiry[key]
    
    def set_with_ttl(self, key: str, value: str, ttl_ms: int) -> None:
        """
        Set key to value with TTL.
        
        Uses monotonic time to avoid system clock issues.
        Time complexity: O(1) average case
        
        Args:
            key: The key to set
            value: The value to store
            ttl_ms: Time to live in milliseconds
        """
        self._data[key] = RedisString(value)
        # Use monotonic time (never goes backwards)
        self._expiry[key] = time.monotonic() + (ttl_ms / 1000.0)
    
    def delete(self, key: str) -> bool:
        """
        Delete a key.
        
        Time complexity: O(1) average case
        
        Args:
            key: The key to delete
        
        Returns:
            True if key existed, False otherwise
        """
        if key in self._data:
            del self._data[key]
            if key in self._expiry:
                del self._expiry[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists and is not expired.
        
        Time complexity: O(1) average case
        
        Args:
            key: The key to check
        
        Returns:
            True if key exists and not expired, False otherwise
        """
        if key not in self._data:
            return False
        
        if self._is_expired(key):
            del self._data[key]
            del self._expiry[key]
            return False
        
        return True
    
    def clear(self) -> None:
        """
        Clear all data.
        
        Time complexity: O(1)
        """
        self._data.clear()
        self._expiry.clear()
    
    @require_type(RedisType.LIST)
    def rpush(self, key: str, *values: str) -> int:
        """
        Append values to list.
        
        Creates list if it doesn't exist.
        Time complexity: O(N) where N is number of values
        
        Args:
            key: The list key
            values: Values to append
        
        Returns:
            Length of list after push
        """
        if key in self._data:
            return self._data[key].rpush(*values)
        else:
            new_list = RedisList()
            length = new_list.rpush(*values)
            self._data[key] = new_list
            return length

    @require_type(RedisType.LIST)
    def lpush(self, key: str, *values: str) -> int:
        """
        Prepend values to list.
        
        Creates list if it doesn't exist.
        Time complexity: O(N) where N is number of values
        
        Args:
            key: The list key
            values: Values to prepend
        
        Returns:
            Length of list after push
        """
        if key in self._data:
            return self._data[key].lpush(*values)
        else:
            new_list = RedisList()
            length = new_list.lpush(*values)
            self._data[key] = new_list
            return length
    
    @require_type(RedisType.LIST)
    def lrange(self, key: str, start: int, stop: int) -> List[str]:
        """
        Get list elements in range.
        
        Time complexity: O(S+N) where S is start offset and N is range size
        
        Rules:
        - Returns empty list if key doesn't exist
        - If stop > length, treats as length (returns till end)
        - If start > stop or start > length, returns empty list
        
        Args:
            key: The list key
            start: Start index (inclusive)
            stop: Stop index (inclusive)
        
        Returns:
            List of elements in range, empty if key doesn't exist
        """
        if key not in self._data:
            return []
        
        return self._data[key].lrange(start, stop)
    
    def __len__(self) -> int:
        """Return number of keys."""
        return len(self._data)
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return key in self._data

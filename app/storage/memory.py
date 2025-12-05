"""In-memory storage implementation using Python dict."""

import time
from typing import Optional, Dict
from .base import BaseStorage


class InMemoryStorage(BaseStorage):
    """
    In-memory storage using Python dict.
    
    This is the primary storage mechanism - same as real Redis.
    Thread-safe with asyncio (single-threaded event loop + GIL).
    Supports TTL (Time To Live) for key expiration.
    """
    
    def __init__(self):
        """Initialize empty storage."""
        self._data: Dict[str, str] = {}
        self._expiry: Dict[str, float] = {}  # key -> monotonic expiration time
    
    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired."""
        if key not in self._expiry:
            return False
        return time.monotonic() > self._expiry[key]
    
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
        
        return self._data.get(key)
    
    def set(self, key: str, value: str) -> None:
        """
        Set key to value.
        
        Time complexity: O(1) average case
        
        Args:
            key: The key to set
            value: The value to store
        """
        self._data[key] = value
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
        self._data[key] = value
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
    
    def __len__(self) -> int:
        """Return number of keys."""
        return len(self._data)
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return key in self._data

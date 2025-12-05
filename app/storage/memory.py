"""In-memory storage implementation using Python dict."""

from typing import Optional, Dict
from .base import BaseStorage


class InMemoryStorage(BaseStorage):
    """
    In-memory storage using Python dict.
    
    This is the primary storage mechanism - same as real Redis.
    Thread-safe with asyncio (single-threaded event loop + GIL).
    """
    
    def __init__(self):
        """Initialize empty storage."""
        self._data: Dict[str, str] = {}
    
    def get(self, key: str) -> Optional[str]:
        """
        Get value by key.
        
        Time complexity: O(1) average case
        
        Args:
            key: The key to look up
        
        Returns:
            Value if key exists, None otherwise
        """
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
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists.
        
        Time complexity: O(1) average case
        
        Args:
            key: The key to check
        
        Returns:
            True if key exists, False otherwise
        """
        return key in self._data
    
    def clear(self) -> None:
        """
        Clear all data.
        
        Time complexity: O(1)
        """
        self._data.clear()
    
    def __len__(self) -> int:
        """Return number of keys."""
        return len(self._data)
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return key in self._data

"""Base storage interface."""

from abc import ABC, abstractmethod
from typing import Optional, List


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
    def lrange(self, key: str, start: int, stop: int) -> List[str]:
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

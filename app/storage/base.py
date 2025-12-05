"""Base storage interface."""

from abc import ABC, abstractmethod
from typing import Optional, Any


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

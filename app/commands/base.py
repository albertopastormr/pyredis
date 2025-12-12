"""Base command interface."""

from abc import ABC, abstractmethod
from typing import Any, List


class BaseCommand(ABC):
    """Abstract base class for all Redis commands."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the command name (e.g., 'PING', 'GET')."""
        pass
    
    @abstractmethod
    async def execute(self, args: List[str]) -> Any:
        """
        Execute the command asynchronously.
        
        For synchronous commands, just implement without await.
        For truly async commands (like BLPOP), use await.
        
        Args:
            args: Command arguments (not including command name)
        
        Returns:
            Command result
        """
        pass
    
    def validate_args(self, args: List[str], min_args: int = None, max_args: int = None) -> None:
        """
        Validate argument count.
        
        Args:
            args: Command arguments
            min_args: Minimum required arguments
            max_args: Maximum allowed arguments
        
        Raises:
            ValueError: If argument count is invalid
        """
        if min_args is not None and len(args) < min_args:
            raise ValueError(f"ERR wrong number of arguments for '{self.name}' command")
        
        if max_args is not None and len(args) > max_args:
            raise ValueError(f"ERR wrong number of arguments for '{self.name}' command")

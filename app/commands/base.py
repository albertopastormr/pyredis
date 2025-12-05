"""Base command class for all Redis commands."""

from abc import ABC, abstractmethod
from typing import Any, List


class BaseCommand(ABC):
    """Base class for all Redis commands."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Command name (e.g., 'PING', 'ECHO')."""
        pass
    
    @abstractmethod
    def execute(self, args: List[str]) -> Any:
        """
        Execute the command with given arguments.
        
        Args:
            args: List of command arguments (not including command name)
        
        Returns:
            Response value to be encoded by RESPEncoder
            - str: Will be encoded as bulk string
            - dict with 'ok': Simple string response
            - dict with 'error': Error response
            - int: Integer response
            - None: Null bulk string
        """
        pass
    
    def validate_args(self, args: List[str], min_args: int = 0, max_args: int = None) -> None:
        """
        Validate argument count.
        
        Args:
            args: Command arguments
            min_args: Minimum required arguments
            max_args: Maximum allowed arguments (None = unlimited)
        
        Raises:
            ValueError: If argument count is invalid
        """
        if len(args) < min_args:
            raise ValueError(
                f"ERR wrong number of arguments for '{self.name.lower()}' command"
            )
        
        if max_args is not None and len(args) > max_args:
            raise ValueError(
                f"ERR wrong number of arguments for '{self.name.lower()}' command"
            )

"""LPOP command implementation."""

from typing import Any, List, Optional
from .base import BaseCommand
from app.storage import get_storage


class LpopCommand(BaseCommand):
    """
    LPOP command - Remove and return elements from the left of a list.
    
    Syntax: LPOP key [count]
    If count is provided, removes that many elements.
    If count > length, removes all elements.
    Returns: Single element (if no count) or array of elements
    Time complexity: O(N) where N is count
    """
    
    @property
    def name(self) -> str:
        return "LPOP"
    
    async def execute(self, args: List[str]) -> Any:
        """
        Execute LPOP command.
        
        Args:
            args: [key] or [key, count]
        
        Returns:
            Single element string (count=1) or list of elements, None if key doesn't exist
        """
        self.validate_args(args, min_args=1, max_args=2)
        
        key = args[0]
        count = 1  # Default count
        
        # Parse count if provided
        if len(args) == 2:
            try:
                count = int(args[1])
                if count < 0:
                    raise ValueError("ERR value is out of range, must be positive")
            except ValueError as e:
                if "out of range" in str(e):
                    raise
                raise ValueError("ERR value is not an integer or out of range")
        
        storage = get_storage()
        result = storage.lpop(key, count)
        
        if result is None:
            return None
        
        if len(args) == 1:
            return result[0] if result else None
        
        return result

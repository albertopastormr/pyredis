"""LLEN command implementation."""

from typing import Any, List
from .base import BaseCommand
from app.storage import get_storage


class LlenCommand(BaseCommand):
    """
    LLEN command - Get length of a list.
    
    Syntax: LLEN key
    Returns: Integer - length of list
    
    Rules:
    - If list doesn't exist, returns 0
    """
    
    @property
    def name(self) -> str:
        return "LLEN"
    
    def execute(self, args: List[str]) -> Any:
        """
        Execute LLEN command.
        
        Args:
            args: [key]
        
        Returns:
            Integer - length of list
        """
        self.validate_args(args, min_args=1, max_args=1)
        
        key = args[0]
        
        storage = get_storage()
        result = storage.llen(key)
        
        return result

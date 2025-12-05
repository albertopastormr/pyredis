"""SET command implementation."""

from typing import Any, List
from .base import BaseCommand
from app.storage import get_storage


class SetCommand(BaseCommand):
    """
    SET command - Set key to hold the string value.
    
    Syntax: SET key value
    
    If key already holds a value, it is overwritten.
    Time complexity: O(1)
    """
    
    @property
    def name(self) -> str:
        return "SET"
    
    def execute(self, args: List[str]) -> Any:
        """
        Execute SET command.
        
        Args:
            args: [key, value]
        
        Returns:
            {'ok': 'OK'} on success
        """
        self.validate_args(args, min_args=2, max_args=2)
        
        key = args[0]
        value = args[1]
        
        storage = get_storage()
        storage.set(key, value)
        
        return {'ok': 'OK'}

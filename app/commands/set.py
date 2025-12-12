"""SET command implementation."""

from typing import Any, List
from .base import BaseCommand
from app.storage import get_storage


class SetCommand(BaseCommand):
    """
    SET command - Set key to hold the string value.
    
    Syntax: SET key value [PX milliseconds]
    
    If key already holds a value, it is overwritten.
    PX option sets expiration time in milliseconds.
    Time complexity: O(1)
    """
    
    @property
    def name(self) -> str:
        return "SET"
    
    async def execute(self, args: List[str]) -> Any:
        """
        Execute SET command.
        
        Args:
            args: [key, value] or [key, value, 'PX', milliseconds]
        
        Returns:
            {'ok': 'OK'} on success
        """
        self.validate_args(args, min_args=2)
        
        key = args[0]
        value = args[1]
        
        if len(args) > 2:
            if len(args) == 4 and args[2].upper() == 'PX':
                try:
                    ttl_ms = int(args[3])
                    if ttl_ms <= 0:
                        raise ValueError("ERR invalid expire time in 'set' command")
                    
                    storage = get_storage()
                    storage.set_with_ttl(key, value, ttl_ms)
                    return {'ok': 'OK'}
                except ValueError as e:
                    if "invalid literal" in str(e):
                        raise ValueError("ERR value is not an integer or out of range")
                    raise
            else:
                raise ValueError("ERR syntax error")
        
        storage = get_storage()
        storage.set(key, value)
        
        return {'ok': 'OK'}

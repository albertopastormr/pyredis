"""BLPOP command implementation."""

import time
import asyncio
from typing import Any, List, Optional
from .base import BaseCommand
from app.storage import get_storage
from app.exceptions import WrongTypeError
from app.blocking import register_waiter, unregister_waiter


class BlpopCommand(BaseCommand):
    """
    BLPOP command - Blocking pop from the left of a list.
    
    Syntax: BLPOP key timeout
    Blocks until an element is available or timeout expires.
    If timeout is 0, blocks indefinitely.
    Returns: Array [key, element] if successful, None if timeout
    """
    
    @property
    def name(self) -> str:
        return "BLPOP"
    
    def _try_pop(self, storage, key: str) -> Optional[List[str]]:
        """
        Try to pop an element from the list.
        
        Returns:
            Array [key, element] if successful, None otherwise
        """
        try:
            result = storage.lpop(key, 1)
            if result and len(result) > 0:
                return [key, result[0]]
        except WrongTypeError:
            pass
        return None
    
    async def execute(self, args: List[str]) -> Any:
        """
        Execute BLPOP command asynchronously (event-driven, no polling).
        
        Args:
            args: [key, timeout]
        
        Returns:
            Array [key, element] if successful, None if timeout expires
        """
        self.validate_args(args, min_args=2, max_args=2)
        
        key = args[0]
        
        try:
            timeout = float(args[1])
            if timeout < 0:
                raise ValueError("ERR timeout is negative")
        except ValueError as e:
            if "negative" in str(e):
                raise
            raise ValueError("ERR timeout is not a float or out of range")
        
        storage = get_storage()
        
        # Try immediate pop
        result = self._try_pop(storage, key)
        if result is not None:
            return result
        
        # List is empty - wait for notification
        event = asyncio.Event()
        register_waiter(key, event)
        
        try:
            if timeout > 0:
                # Wait with timeout
                await asyncio.wait_for(event.wait(), timeout=timeout)
            else:
                # Wait indefinitely
                await event.wait()
            
            # We were notified - try to pop
            result = self._try_pop(storage, key)
            return result or None
            
        except asyncio.TimeoutError:
            # Timeout expired
            return None
        finally:
            # Always unregister
            unregister_waiter(key, event)

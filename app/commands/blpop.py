"""BLPOP command implementation."""

import time
from typing import Any, List, Optional
from .base import BaseCommand
from app.storage import get_storage
from app.exceptions import WrongTypeError


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
    
    def execute(self, args: List[str]) -> Any:
        """
        Execute BLPOP command.
        
        Args:
            args: [key, timeout]
        
        Returns:
            Array [key, element] if successful, None if timeout expires
        """
        self.validate_args(args, min_args=2, max_args=2)
        
        key = args[0]
        
        # Parse timeout
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
        
        start_time = time.monotonic()
        poll_interval = 0.1  # Poll every 100ms
        
        while True:
            if timeout > 0:
                elapsed = time.monotonic() - start_time
                if elapsed >= timeout:
                    return None
            
            result = self._try_pop(storage, key)
            if result is not None:
                return result
            
            if timeout > 0:
                remaining = timeout - (time.monotonic() - start_time)
                sleep_time = min(poll_interval, remaining)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            else:
                time.sleep(poll_interval)
                if time.monotonic() - start_time > 3600:  # 1 hour max
                    return None

"""Blocking operations notification system for async commands."""

import asyncio
from typing import Dict, List
from collections import defaultdict


class BlockingNotifier:
    """
    Manages notifications for blocking commands like BLPOP.
    
    When a client executes BLPOP and the list is empty, it registers
    an event to wait on. When RPUSH/LPUSH adds items, it notifies
    all waiting clients.
    """
    
    def __init__(self):
        # Maps key -> list of (event, task_id) tuples
        self._waiting_clients: Dict[str, List[tuple]] = defaultdict(list)
    
    def register_waiter(self, key: str, event: asyncio.Event, task_id: str = None) -> None:
        """
        Register a client waiting on a key.
        
        Args:
            key: The key being waited on
            event: Asyncio event to set when data is available
            task_id: Optional identifier for debugging
        """
        self._waiting_clients[key].append((event, task_id))
    
    def unregister_waiter(self, key: str, event: asyncio.Event) -> None:
        """
        Unregister a client that's no longer waiting.
        
        Args:
            key: The key that was being waited on
            event: The event to remove
        """
        if key in self._waiting_clients:
            self._waiting_clients[key] = [
                (e, tid) for e, tid in self._waiting_clients[key] if e != event
            ]
            # Clean up empty lists
            if not self._waiting_clients[key]:
                del self._waiting_clients[key]
    
    def notify_key(self, key: str, available_count: int = 1) -> int:
        """
        Notify all clients waiting on a key that data is available.
        
        Args:
            key: The key that now has data
        
        Returns:
            Number of clients notified
        """
        if key not in self._waiting_clients:
            return 0
        waiters = self._waiting_clients[key]
        count = 0
        
        while waiters and count < available_count:
            event, task_id = waiters.pop(0)
            event.set()
            count += 1
            
        if not waiters:
            del self._waiting_clients[key]
        
        return count
    
    def get_waiter_count(self, key: str) -> int:
        """Get the number of clients waiting on a key."""
        return len(self._waiting_clients.get(key, []))


# Global singleton instance
_notifier = BlockingNotifier()


def register_waiter(key: str, event: asyncio.Event, task_id: str = None) -> None:
    """Register a client waiting on a key."""
    _notifier.register_waiter(key, event, task_id)


def unregister_waiter(key: str, event: asyncio.Event) -> None:
    """Unregister a client that's no longer waiting."""
    _notifier.unregister_waiter(key, event)


def notify_key(key: str, available_count: int = 1) -> int:
    """Notify all clients waiting on a key. Returns number notified."""
    return _notifier.notify_key(key, available_count)


def get_waiter_count(key: str) -> int:
    """Get the number of clients waiting on a key."""
    return _notifier.get_waiter_count(key)

"""
Storage layer - manages data persistence.

This module provides storage backends for Redis data.
Currently supports in-memory storage (like real Redis).

Future backends could include:
- Persistent storage (RDB-style snapshots)
- AOF (Append-Only File) logging
- Hybrid (memory + persistence)
"""

from .base import BaseStorage
from .memory import InMemoryStorage

# Global storage instance (singleton pattern)
_storage_instance: BaseStorage = None


def get_storage() -> BaseStorage:
    """
    Get the global storage instance.
    
    Uses singleton pattern to ensure single storage instance
    across the application.
    
    Returns:
        The global storage instance
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = InMemoryStorage()
    return _storage_instance


def set_storage(storage: BaseStorage) -> None:
    """
    Set a custom storage backend.
    
    Useful for:
    - Testing (inject mock storage)
    - Different backends (persistent, distributed, etc.)
    
    Args:
        storage: Storage instance to use
    """
    global _storage_instance
    _storage_instance = storage


def reset_storage() -> None:
    """
    Reset storage to new instance.
    
    Useful for:
    - Testing (clean slate between tests)
    - FLUSHALL command implementation
    """
    global _storage_instance
    _storage_instance = InMemoryStorage()


__all__ = [
    'BaseStorage',
    'InMemoryStorage',
    'get_storage',
    'set_storage',
    'reset_storage',
]

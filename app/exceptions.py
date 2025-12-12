"""Custom exceptions for Redis operations."""


class RedisError(Exception):
    """Base exception for all Redis errors."""
    pass


class WrongTypeError(ValueError):
    """
    Exception raised when operation is performed on wrong data type.
    
    Inherits from ValueError for backward compatibility with existing code
    that catches ValueError for Redis errors.
    """
    
    def __init__(self, message="WRONGTYPE Operation against a key holding the wrong kind of value"):
        self.message = message
        super().__init__(self.message)

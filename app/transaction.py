"""Transaction management for Redis MULTI/EXEC/DISCARD commands."""

from typing import Any, Dict, List, Optional


class TransactionContext:
    """
    Manages transaction state for a single connection.
    
    Tracks whether a connection is in a transaction and queues commands
    that should be executed atomically on EXEC.
    """
    
    def __init__(self):
        """Initialize transaction context."""
        self._in_transaction = False
        self._queued_commands: List[tuple[str, List[str]]] = []
    
    @property
    def in_transaction(self) -> bool:
        """Check if currently in a transaction."""
        return self._in_transaction
    
    def start_transaction(self) -> None:
        """Start a new transaction (MULTI command)."""
        self._in_transaction = True
        self._queued_commands = []
    
    def queue_command(self, command_name: str, args: List[str]) -> None:
        """
        Queue a command for later execution.
        
        Args:
            command_name: Name of the command
            args: Command arguments
        """
        self._queued_commands.append((command_name, args))
    
    def get_queued_commands(self) -> List[tuple[str, List[str]]]:
        """
        Get all queued commands.
        
        Returns:
            List of (command_name, args) tuples
        """
        return self._queued_commands.copy()
    
    def clear_transaction(self) -> None:
        """Clear transaction state (used by EXEC or DISCARD)."""
        self._in_transaction = False
        self._queued_commands = []
    
    def discard_transaction(self) -> None:
        """Discard the current transaction (DISCARD command)."""
        self.clear_transaction()


# Global registry of transaction contexts per connection
# Key: connection identifier (e.g., peername tuple)
_transaction_contexts: Dict[Any, TransactionContext] = {}


def get_transaction_context(connection_id: Any) -> TransactionContext:
    """
    Get or create a transaction context for a connection.
    
    Args:
        connection_id: Unique identifier for the connection
        
    Returns:
        TransactionContext for this connection
    """
    if connection_id not in _transaction_contexts:
        _transaction_contexts[connection_id] = TransactionContext()
    return _transaction_contexts[connection_id]


def remove_transaction_context(connection_id: Any) -> None:
    """
    Remove transaction context when connection closes.
    
    Args:
        connection_id: Unique identifier for the connection
    """
    if connection_id in _transaction_contexts:
        del _transaction_contexts[connection_id]

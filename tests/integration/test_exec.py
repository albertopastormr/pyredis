"""Integration tests for EXEC command."""

import asyncio

import pytest

from app.handler import execute_command
from app.storage import get_storage, reset_storage
from app.transaction import get_transaction_context


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up storage and transactions after each test."""
    reset_storage()
    yield
    reset_storage()
    from app.transaction import _transaction_contexts
    _transaction_contexts.clear()


class TestExecIntegration:
    """Integration tests for EXEC command."""

    def test_exec_empty_transaction(self):
        """EXEC with no queued commands returns empty array."""
        connection_id = ("127.0.0.1", 20001)
        
        asyncio.run(execute_command(["MULTI"], connection_id=connection_id))
        result = asyncio.run(execute_command(["EXEC"], connection_id=connection_id))
        
        assert result == []

    def test_exec_executes_queued_commands(self):
        """EXEC executes all queued commands and returns their results."""
        connection_id = ("127.0.0.1", 20002)
        storage = get_storage()
        
        # Start transaction
        asyncio.run(execute_command(["MULTI"], connection_id=connection_id))
        
        # Queue commands
        asyncio.run(execute_command(["SET", "foo", "100"], connection_id=connection_id))
        asyncio.run(execute_command(["INCR", "foo"], connection_id=connection_id))
        asyncio.run(execute_command(["GET", "foo"], connection_id=connection_id))
        
        # Execute transaction
        result = asyncio.run(execute_command(["EXEC"], connection_id=connection_id))
        
        # Verify results
        assert len(result) == 3
        assert result[0] == {"ok": "OK"}  # SET result
        assert result[1] == 101  # INCR result
        assert result[2] == "101"  # GET result
        
        # Verify data was actually stored
        assert storage.get("foo") == "101"

    def test_exec_clears_transaction_state(self):
        """EXEC clears transaction state after execution."""
        connection_id = ("127.0.0.1", 20003)
        
        asyncio.run(execute_command(["MULTI"], connection_id=connection_id))
        asyncio.run(execute_command(["SET", "key", "value"], connection_id=connection_id))
        asyncio.run(execute_command(["EXEC"], connection_id=connection_id))
        
        # Verify transaction is no longer active
        ctx = get_transaction_context(connection_id)
        assert ctx.in_transaction is False
        
        # Next command should execute normally, not queue
        result = asyncio.run(execute_command(["SET", "key2", "value2"], connection_id=connection_id))
        assert result == {"ok": "OK"}

    def test_exec_without_multi_fails(self):
        """EXEC without MULTI raises error."""
        connection_id = ("127.0.0.1", 20004)
        
        with pytest.raises(ValueError, match="ERR EXEC without MULTI"):
            asyncio.run(execute_command(["EXEC"], connection_id=connection_id))

    def test_exec_complex_transaction(self):
        """EXEC handles complex transaction with multiple operations."""
        connection_id = ("127.0.0.1", 20005)
        storage = get_storage()
        
        asyncio.run(execute_command(["MULTI"], connection_id=connection_id))
        asyncio.run(execute_command(["SET", "counter", "0"], connection_id=connection_id))
        asyncio.run(execute_command(["INCR", "counter"], connection_id=connection_id))
        asyncio.run(execute_command(["INCR", "counter"], connection_id=connection_id))
        asyncio.run(execute_command(["INCR", "counter"], connection_id=connection_id))
        asyncio.run(execute_command(["GET", "counter"], connection_id=connection_id))
        
        result = asyncio.run(execute_command(["EXEC"], connection_id=connection_id))
        
        assert len(result) == 5
        assert result[0] == {"ok": "OK"}
        assert result[1] == 1
        assert result[2] == 2
        assert result[3] == 3
        assert result[4] == "3"
        assert storage.get("counter") == "3"

    def test_exec_isolated_between_connections(self):
        """Transactions on different connections are independent."""
        conn1 = ("127.0.0.1", 30001)
        conn2 = ("127.0.0.1", 30002)
        storage = get_storage()
        
        # Start transactions on both connections
        asyncio.run(execute_command(["MULTI"], connection_id=conn1))
        asyncio.run(execute_command(["MULTI"], connection_id=conn2))
        
        # Queue different commands
        asyncio.run(execute_command(["SET", "key1", "value1"], connection_id=conn1))
        asyncio.run(execute_command(["SET", "key2", "value2"], connection_id=conn2))
        
        # Execute first transaction
        result1 = asyncio.run(execute_command(["EXEC"], connection_id=conn1))
        assert len(result1) == 1
        assert storage.get("key1") == "value1"
        assert storage.get("key2") is None  # Second transaction not executed yet
        
        # Execute second transaction
        result2 = asyncio.run(execute_command(["EXEC"], connection_id=conn2))
        assert len(result2) == 1
        assert storage.get("key2") == "value2"

"""Integration tests for DISCARD command."""

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


class TestDiscardIntegration:
    """Integration tests for DISCARD command."""

    def test_discard_clears_queued_commands(self):
        """DISCARD removes all queued commands."""
        connection_id = ("127.0.0.1", 20006)
        storage = get_storage()

        asyncio.run(execute_command(["MULTI"], connection_id=connection_id))
        asyncio.run(execute_command(["SET", "foo", "bar"], connection_id=connection_id))
        asyncio.run(execute_command(["INCR", "counter"], connection_id=connection_id))

        result = asyncio.run(execute_command(["DISCARD"], connection_id=connection_id))

        assert result == {"ok": "OK"}

        # Verify commands were not executed
        assert storage.get("foo") is None
        assert storage.get("counter") is None

    def test_discard_clears_transaction_state(self):
        """DISCARD clears transaction state."""
        connection_id = ("127.0.0.1", 20007)

        asyncio.run(execute_command(["MULTI"], connection_id=connection_id))
        asyncio.run(execute_command(["SET", "key", "value"], connection_id=connection_id))
        asyncio.run(execute_command(["DISCARD"], connection_id=connection_id))

        # Verify transaction is no longer active
        ctx = get_transaction_context(connection_id)
        assert ctx.in_transaction is False

        # Next command should execute normally
        result = asyncio.run(
            execute_command(["SET", "key2", "value2"], connection_id=connection_id)
        )
        assert result == {"ok": "OK"}

    def test_discard_without_multi_fails(self):
        """DISCARD without MULTI raises error."""
        connection_id = ("127.0.0.1", 20008)

        with pytest.raises(ValueError, match="ERR DISCARD without MULTI"):
            asyncio.run(execute_command(["DISCARD"], connection_id=connection_id))

    def test_discard_empty_transaction(self):
        """DISCARD works with empty transaction."""
        connection_id = ("127.0.0.1", 20009)

        asyncio.run(execute_command(["MULTI"], connection_id=connection_id))
        result = asyncio.run(execute_command(["DISCARD"], connection_id=connection_id))

        assert result == {"ok": "OK"}
        ctx = get_transaction_context(connection_id)
        assert ctx.in_transaction is False

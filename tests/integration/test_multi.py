"""Integration tests for MULTI command."""

import asyncio

import pytest

from app.handler import execute_command
from app.transaction import get_transaction_context, remove_transaction_context


@pytest.fixture(autouse=True)
def cleanup_transactions():
    """Clean up any transaction state after each test."""
    yield
    # Clean up all transaction contexts
    from app.transaction import _transaction_contexts

    _transaction_contexts.clear()


class TestMultiIntegration:
    """Integration tests for MULTI command."""

    def test_multi_starts_transaction(self):
        """MULTI command starts a transaction."""
        connection_id = ("127.0.0.1", 12345)

        result = asyncio.run(execute_command(["MULTI"], connection_id=connection_id))

        assert result == {"ok": "OK"}
        ctx = get_transaction_context(connection_id)
        assert ctx.in_transaction is True

    def test_commands_queued_after_multi(self):
        """Commands after MULTI are queued, not executed."""
        connection_id = ("127.0.0.1", 12346)

        # Start transaction
        asyncio.run(execute_command(["MULTI"], connection_id=connection_id))

        # These commands should be queued
        result1 = asyncio.run(execute_command(["SET", "foo", "bar"], connection_id=connection_id))
        result2 = asyncio.run(execute_command(["GET", "foo"], connection_id=connection_id))
        result3 = asyncio.run(execute_command(["INCR", "counter"], connection_id=connection_id))

        assert result1 == {"queued": "QUEUED"}
        assert result2 == {"queued": "QUEUED"}
        assert result3 == {"queued": "QUEUED"}

        # Verify commands were queued
        ctx = get_transaction_context(connection_id)
        queued = ctx.get_queued_commands()
        assert len(queued) == 3
        assert queued[0] == ("SET", ["foo", "bar"])
        assert queued[1] == ("GET", ["foo"])
        assert queued[2] == ("INCR", ["counter"])

    def test_multi_case_insensitive(self):
        """MULTI command is case-insensitive."""
        connection_id1 = ("127.0.0.1", 12347)
        connection_id2 = ("127.0.0.1", 12348)
        connection_id3 = ("127.0.0.1", 12349)

        result1 = asyncio.run(execute_command(["MULTI"], connection_id=connection_id1))
        result2 = asyncio.run(execute_command(["multi"], connection_id=connection_id2))
        result3 = asyncio.run(execute_command(["Multi"], connection_id=connection_id3))

        assert result1 == {"ok": "OK"}
        assert result2 == {"ok": "OK"}
        assert result3 == {"ok": "OK"}

    def test_multi_with_args_error(self):
        """MULTI with arguments raises error."""
        connection_id = ("127.0.0.1", 12350)

        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(execute_command(["MULTI", "arg"], connection_id=connection_id))

    def test_commands_execute_normally_without_multi(self):
        """Commands execute normally when not in a transaction."""
        connection_id = ("127.0.0.1", 12351)

        # Execute commands without MULTI
        result = asyncio.run(
            execute_command(["SET", "testkey", "testvalue"], connection_id=connection_id)
        )

        # Should return OK, not QUEUED
        assert result == {"ok": "OK"}

        # Verify not in transaction
        ctx = get_transaction_context(connection_id)
        assert ctx.in_transaction is False

"""Unit tests for MULTI command."""

import asyncio

import pytest

from app.commands.multi import MultiCommand
from app.transaction import get_transaction_context


@pytest.fixture
def multi_command():
    """Fixture providing a MULTI command instance."""
    return MultiCommand()


class TestMultiCommand:
    """Test MULTI command in isolation."""

    def test_multi_returns_ok(self, multi_command):
        """MULTI command returns OK."""
        result = asyncio.run(multi_command.execute([]))

        assert result == {"ok": "OK"}

    def test_multi_with_connection_id(self, multi_command):
        """MULTI with connection_id starts a transaction."""
        connection_id = ("127.0.0.1", 12345)
        result = asyncio.run(multi_command.execute([], connection_id=connection_id))

        assert result == {"ok": "OK"}

        # Verify transaction was started
        ctx = get_transaction_context(connection_id)
        assert ctx.in_transaction is True

    def test_multi_with_args_fails(self, multi_command):
        """MULTI with arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(multi_command.execute(["extra"]))

    def test_command_name(self, multi_command):
        """Command has correct name."""
        assert multi_command.name == "MULTI"

    def test_multi_without_connection_id(self, multi_command):
        """MULTI without connection_id still returns OK."""
        result = asyncio.run(multi_command.execute([]))
        assert result == {"ok": "OK"}

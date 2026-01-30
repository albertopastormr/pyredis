"""Unit tests for DISCARD command."""

import asyncio

import pytest

from app.commands.discard import DiscardCommand


@pytest.fixture
def discard_command():
    """Fixture providing a DISCARD command instance."""
    return DiscardCommand()


class TestDiscardCommand:
    """Test DISCARD command in isolation."""

    def test_discard_without_multi_fails(self, discard_command):
        """DISCARD without MULTI raises error."""
        connection_id = ("127.0.0.1", 10003)
        
        with pytest.raises(ValueError, match="ERR DISCARD without MULTI"):
            asyncio.run(discard_command.execute([], connection_id=connection_id))

    def test_discard_without_connection_id_fails(self, discard_command):
        """DISCARD without connection_id raises error."""
        with pytest.raises(ValueError, match="ERR DISCARD without MULTI"):
            asyncio.run(discard_command.execute([]))

    def test_discard_with_args_fails(self, discard_command):
        """DISCARD with arguments raises error."""
        connection_id = ("127.0.0.1", 10004)
        
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(discard_command.execute(["arg"], connection_id=connection_id))

    def test_command_name(self, discard_command):
        """Command has correct name."""
        assert discard_command.name == "DISCARD"

    def test_bypasses_transaction_queue(self, discard_command):
        """DISCARD bypasses transaction queuing."""
        assert discard_command.bypasses_transaction_queue is True

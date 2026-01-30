"""Unit tests for EXEC command."""

import asyncio

import pytest

from app.commands.exec import ExecCommand


@pytest.fixture
def exec_command():
    """Fixture providing an EXEC command instance."""
    return ExecCommand()


class TestExecCommand:
    """Test EXEC command in isolation."""

    def test_exec_without_multi_fails(self, exec_command):
        """EXEC without MULTI raises error."""
        connection_id = ("127.0.0.1", 10001)
        
        with pytest.raises(ValueError, match="ERR EXEC without MULTI"):
            asyncio.run(exec_command.execute([], connection_id=connection_id))

    def test_exec_without_connection_id_fails(self, exec_command):
        """EXEC without connection_id raises error."""
        with pytest.raises(ValueError, match="ERR EXEC without MULTI"):
            asyncio.run(exec_command.execute([]))

    def test_exec_with_args_fails(self, exec_command):
        """EXEC with arguments raises error."""
        connection_id = ("127.0.0.1", 10002)
        
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(exec_command.execute(["arg"], connection_id=connection_id))

    def test_command_name(self, exec_command):
        """Command has correct name."""
        assert exec_command.name == "EXEC"

    def test_bypasses_transaction_queue(self, exec_command):
        """EXEC bypasses transaction queuing."""
        assert exec_command.bypasses_transaction_queue is True

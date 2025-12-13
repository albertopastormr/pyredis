"""Unit tests for execute_command function."""

import asyncio

import pytest

# Import the REAL async version before monkey-patching
from app.handler import execute_command as handler_execute_command


class TestExecuteCommand:
    """Test execute_command with various inputs."""

    def test_execute_valid_ping(self):
        """Execute a valid PING command."""
        result = asyncio.run(handler_execute_command(["PING"]))
        assert result == {"ok": "PONG"}

    def test_execute_valid_echo(self):
        """Execute a valid ECHO command with argument."""
        result = asyncio.run(handler_execute_command(["ECHO", "hello"]))
        assert result == "hello"

    def test_execute_empty_command(self):
        """Execute with empty list raises error."""
        with pytest.raises(ValueError, match="Invalid command format"):
            asyncio.run(handler_execute_command([]))

    def test_execute_non_list_command(self):
        """Execute with non-list raises error."""
        with pytest.raises(ValueError, match="Invalid command format"):
            asyncio.run(handler_execute_command("PING"))

    def test_execute_unknown_command(self):
        """Execute unknown command raises error."""
        with pytest.raises(ValueError, match="unknown command"):
            asyncio.run(handler_execute_command(["NONEXISTENT"]))

    def test_execute_case_insensitive(self):
        """Commands are case-insensitive."""
        result = asyncio.run(handler_execute_command(["ping"]))
        assert result == {"ok": "PONG"}

    def test_execute_with_args(self):
        """Execute command with multiple arguments."""
        result = asyncio.run(handler_execute_command(["SET", "key", "value"]))
        assert result == {"ok": "OK"}

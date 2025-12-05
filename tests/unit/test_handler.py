"""Tests for handler module."""

import pytest

from app.handler import execute_command


class TestExecuteCommand:
    """Test command execution logic."""
    
    def test_execute_valid_ping(self):
        """Execute valid PING command."""
        command = ['PING']
        result = execute_command(command)
        assert result == {'ok': 'PONG'}
    
    def test_execute_valid_echo(self):
        """Execute valid ECHO command."""
        command = ['ECHO', 'hello']
        result = execute_command(command)
        assert result == 'hello'
    
    def test_execute_empty_command(self):
        """Empty command raises error."""
        with pytest.raises(ValueError, match="Invalid command format"):
            execute_command([])
    
    def test_execute_non_list_command(self):
        """Non-list command raises error."""
        with pytest.raises(ValueError, match="Invalid command format"):
            execute_command("PING")
    
    def test_execute_unknown_command(self):
        """Unknown command raises error."""
        command = ['UNKNOWN']
        with pytest.raises(ValueError, match="unknown command"):
            execute_command(command)
    
    def test_execute_case_insensitive(self):
        """Commands are case-insensitive."""
        result1 = execute_command(['PING'])
        result2 = execute_command(['ping'])
        result3 = execute_command(['PiNg'])
        
        assert result1 == result2 == result3
    
    def test_execute_with_args(self):
        """Command with arguments works."""
        command = ['ECHO', 'test', 'extra']
        # Should raise validation error (ECHO takes exactly 1 arg)
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(command)

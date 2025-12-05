"""Tests for command infrastructure."""

import pytest

from app.commands import CommandRegistry, BaseCommand
from app.commands.ping import PingCommand
from app.commands.echo import EchoCommand


class TestCommandRegistry:
    """Test the command registry."""
    
    def test_registry_has_commands(self):
        """Registry should have PING and ECHO registered."""
        commands = CommandRegistry.get_all_commands()
        assert 'PING' in commands
        assert 'ECHO' in commands
    
    def test_execute_ping(self):
        """Registry can execute PING command."""
        result = CommandRegistry.execute('PING', [])
        assert result == {'ok': 'PONG'}
    
    def test_execute_echo(self):
        """Registry can execute ECHO command."""
        result = CommandRegistry.execute('ECHO', ['hello'])
        assert result == 'hello'
    
    def test_execute_unknown_command(self):
        """Registry raises error for unknown command."""
        with pytest.raises(ValueError, match="unknown command"):
            CommandRegistry.execute('UNKNOWN', [])
    
    def test_case_insensitive(self):
        """Commands are case-insensitive."""
        result1 = CommandRegistry.execute('PING', [])
        result2 = CommandRegistry.execute('ping', [])
        result3 = CommandRegistry.execute('PiNg', [])
        
        assert result1 == result2 == result3

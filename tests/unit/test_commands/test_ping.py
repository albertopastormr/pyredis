"""Tests for PING command."""

import pytest

from app.commands.ping import PingCommand


@pytest.fixture
def ping_command():
    """Fixture providing a PING command instance."""
    return PingCommand()


class TestPingCommand:
    """Test PING command implementation."""
    
    def test_ping_without_args(self, ping_command):
        """PING without arguments returns PONG."""
        result = ping_command.execute([])
        assert result == {'ok': 'PONG'}
    
    def test_ping_with_message(self, ping_command):
        """PING with message returns the message."""
        result = ping_command.execute(['hello'])
        assert result == 'hello'
    
    def test_ping_with_long_message(self, ping_command):
        """PING with long message works."""
        message = 'a' * 1000
        result = ping_command.execute([message])
        assert result == message
    
    def test_ping_too_many_args(self, ping_command):
        """PING with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            ping_command.execute(['arg1', 'arg2'])
    
    def test_command_name(self, ping_command):
        """Command has correct name."""
        assert ping_command.name == 'PING'

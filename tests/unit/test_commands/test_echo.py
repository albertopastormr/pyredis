"""Tests for ECHO command."""

import pytest

from app.commands.echo import EchoCommand


@pytest.fixture
def echo_command():
    """Fixture providing an ECHO command instance."""
    return EchoCommand()


class TestEchoCommand:
    """Test ECHO command implementation."""
    
    def test_echo_simple_string(self, echo_command):
        """ECHO returns the argument."""
        result = echo_command.execute(['hello'])
        assert result == 'hello'
    
    def test_echo_with_spaces(self, echo_command):
        """ECHO handles strings with spaces."""
        result = echo_command.execute(['hello world'])
        assert result == 'hello world'
    
    def test_echo_empty_string(self, echo_command):
        """ECHO can echo empty string."""
        result = echo_command.execute([''])
        assert result == ''
    
    def test_echo_special_chars(self, echo_command):
        """ECHO handles special characters."""
        message = 'hello\r\n\t世界'
        result = echo_command.execute([message])
        assert result == message
    
    def test_echo_no_args(self, echo_command):
        """ECHO without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            echo_command.execute([])
    
    def test_echo_too_many_args(self, echo_command):
        """ECHO with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            echo_command.execute(['arg1', 'arg2'])
    
    def test_command_name(self, echo_command):
        """Command has correct name."""
        assert echo_command.name == 'ECHO'

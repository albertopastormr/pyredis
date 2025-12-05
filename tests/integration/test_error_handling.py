"""Integration tests for error handling."""

import pytest

from app.resp import RESPParser, RESPEncoder
from app.handler import execute_command


class TestErrorHandling:
    """Test error handling across the system."""
    
    def test_unknown_command(self):
        """Unknown command returns error."""
        request = b"*1\r\n$7\r\nUNKNOWN\r\n"
        
        command = RESPParser.parse(request)
        with pytest.raises(ValueError, match="unknown command"):
            execute_command(command)
    
    def test_wrong_number_of_args_echo(self):
        """ECHO with wrong args returns error."""
        # ECHO with no args
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['ECHO'])
        
        # ECHO with too many args
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['ECHO', 'arg1', 'arg2'])
    
    def test_wrong_number_of_args_set(self):
        """SET with wrong args returns error."""
        # SET with no args
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['SET'])
        
        # SET with one arg
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['SET', 'key'])
        
        # SET with too many args
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['SET', 'key', 'value', 'extra'])
    
    def test_wrong_number_of_args_get(self):
        """GET with wrong args returns error."""
        # GET with no args
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['GET'])
        
        # GET with too many args
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['GET', 'key', 'extra'])
    
    def test_case_insensitive_commands(self):
        """Commands are case-insensitive."""
        # SET in different cases
        execute_command(['set', 'key1', 'value'])
        execute_command(['Set', 'key2', 'value'])
        execute_command(['SET', 'key3', 'value'])
        
        # GET in different cases
        assert execute_command(['get', 'key1']) == 'value'
        assert execute_command(['Get', 'key2']) == 'value'
        assert execute_command(['GET', 'key3']) == 'value'

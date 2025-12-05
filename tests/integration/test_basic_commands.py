"""Integration tests for basic commands (PING, ECHO)."""

import pytest

from app.resp import RESPParser, RESPEncoder
from app.handler import execute_command


class TestPingIntegration:
    """Test PING command full flow."""
    
    def test_ping_request_response(self):
        """Complete PING flow: parse → execute → encode."""
        # Client request
        request = b"*1\r\n$4\r\nPING\r\n"
        
        # Parse
        command = RESPParser.parse(request)
        assert command == ['PING']
        
        # Execute
        result = execute_command(command)
        assert result == {'ok': 'PONG'}
        
        # Encode response
        response = RESPEncoder.encode(result)
        assert response == b"+PONG\r\n"
    
    def test_ping_with_message(self):
        """PING with message full flow."""
        # PING hello
        request = b"*2\r\n$4\r\nPING\r\n$5\r\nhello\r\n"
        
        command = RESPParser.parse(request)
        result = execute_command(command)
        response = RESPEncoder.encode(result)
        
        assert response == b"$5\r\nhello\r\n"


class TestEchoIntegration:
    """Test ECHO command full flow."""
    
    def test_echo_request_response(self):
        """Complete ECHO flow: parse → execute → encode."""
        # Client request: ECHO hello
        request = b"*2\r\n$4\r\nECHO\r\n$5\r\nhello\r\n"
        
        # Parse
        command = RESPParser.parse(request)
        assert command == ['ECHO', 'hello']
        
        # Execute
        result = execute_command(command)
        assert result == 'hello'
        
        # Encode response
        response = RESPEncoder.encode(result)
        assert response == b"$5\r\nhello\r\n"
    
    def test_echo_special_chars(self):
        """ECHO with special characters."""
        message = "hello\r\nworld"
        request = RESPEncoder.encode(['ECHO', message])
        
        command = RESPParser.parse(request)
        result = execute_command(command)
        response = RESPEncoder.encode(result)
        
        # Verify round trip
        decoded = RESPParser.parse(response)
        assert decoded == message

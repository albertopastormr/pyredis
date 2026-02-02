"""Integration tests for INFO command."""

import pytest

from app.config import Role, ServerConfig
from app.resp import RESPEncoder, RESPParser
from tests.helpers import execute_command


@pytest.fixture(autouse=True)
def reset_server_config():
    """Reset server config before each test."""
    ServerConfig.reset()
    ServerConfig.initialize(role=Role.MASTER)
    yield
    ServerConfig.reset()


class TestInfoIntegration:
    """Test INFO command full flow: parse → execute → encode."""

    def test_info_replication_full_flow(self):
        """Complete INFO replication flow."""
        # Client request: INFO replication
        request = b"*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n"

        # Parse
        command = RESPParser.parse(request)
        assert command == ["INFO", "replication"]

        # Execute
        result = execute_command(command)
        assert isinstance(result, str)
        assert "# Replication" in result
        assert "role:master" in result
        assert "master_replid:8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb" in result
        assert "master_repl_offset:0" in result

        # Encode response (should be bulk string)
        response = RESPEncoder.encode(result)
        
        # Verify it's a valid RESP bulk string
        assert response.startswith(b"$")
        assert b"# Replication\nrole:master" in response
        assert b"master_replid:8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb" in response
        assert b"master_repl_offset:0" in response

    def test_info_replication_slave_role(self):
        """INFO replication returns slave role when configured as replica."""
        # Configure as slave
        ServerConfig.initialize(
            role=Role.SLAVE,
            master_host="localhost",
            master_port=6379,
        )

        request = b"*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n"
        command = RESPParser.parse(request)
        result = execute_command(command)

        assert isinstance(result, str)
        assert "# Replication" in result
        assert "role:slave" in result

        # Encode and verify
        response = RESPEncoder.encode(result)
        assert response.startswith(b"$")
        assert b"role:slave" in response

    def test_info_no_args_full_flow(self):
        """INFO without arguments full flow."""
        # Client request: INFO
        request = b"*1\r\n$4\r\nINFO\r\n"

        # Parse
        command = RESPParser.parse(request)
        assert command == ["INFO"]

        # Execute
        result = execute_command(command)
        assert isinstance(result, str)
        assert "role:master" in result

        # Encode and verify
        response = RESPEncoder.encode(result)
        assert response.startswith(b"$")

    def test_info_case_insensitive_integration(self):
        """INFO section is case-insensitive in full flow."""
        # Test with uppercase
        request = b"*2\r\n$4\r\nINFO\r\n$11\r\nREPLICATION\r\n"
        command = RESPParser.parse(request)
        result = execute_command(command)
        
        assert "role:master" in result

    def test_info_unsupported_section_integration(self):
        """INFO with unsupported section returns empty string."""
        # Client request: INFO memory
        request = b"*2\r\n$4\r\nINFO\r\n$6\r\nmemory\r\n"

        command = RESPParser.parse(request)
        result = execute_command(command)
        
        # Should return empty string
        assert result == ""

        # Encode and verify it's a valid bulk string
        response = RESPEncoder.encode(result)
        assert response == b"$0\r\n\r\n"

    def test_info_response_parseable(self):
        """INFO response can be parsed back."""
        request = b"*2\r\n$4\r\nINFO\r\n$11\r\nreplication\r\n"
        
        command = RESPParser.parse(request)
        result = execute_command(command)
        response = RESPEncoder.encode(result)
        
        # Parse the response back
        parsed_result = RESPParser.parse(response)
        assert isinstance(parsed_result, str)
        assert "role:master" in parsed_result
        assert parsed_result == result


"""Integration tests for storage commands (GET, SET)."""

from app.resp import RESPEncoder, RESPParser
from app.storage import get_storage
from tests.helpers import execute_command


class TestSetGetIntegration:
    """Test SET/GET command integration."""

    def test_set_then_get(self):
        """SET a key, then GET it back (full flow)."""
        # SET mykey myvalue
        set_request = b"*3\r\n$3\r\nSET\r\n$5\r\nmykey\r\n$7\r\nmyvalue\r\n"

        # Parse and execute SET
        set_command = RESPParser.parse(set_request)
        set_result = execute_command(set_command)
        set_response = RESPEncoder.encode(set_result)

        assert set_response == b"+OK\r\n"

        # GET mykey
        get_request = b"*2\r\n$3\r\nGET\r\n$5\r\nmykey\r\n"

        # Parse and execute GET
        get_command = RESPParser.parse(get_request)
        get_result = execute_command(get_command)
        get_response = RESPEncoder.encode(get_result)

        assert get_response == b"$7\r\nmyvalue\r\n"

    def test_get_non_existent(self):
        """GET non-existent key returns nil."""
        # GET nonexistent
        request = b"*2\r\n$3\r\nGET\r\n$11\r\nnonexistent\r\n"

        command = RESPParser.parse(request)
        result = execute_command(command)
        response = RESPEncoder.encode(result)

        # nil is encoded as $-1\r\n
        assert response == b"$-1\r\n"

    def test_set_overwrites(self):
        """SET overwrites existing key."""
        # SET key value1
        execute_command(["SET", "key", "value1"])

        # SET key value2
        execute_command(["SET", "key", "value2"])

        # GET key
        result = execute_command(["GET", "key"])
        assert result == "value2"

    def test_multiple_keys(self):
        """Multiple SET/GET operations."""
        # Set multiple keys
        execute_command(["SET", "user:1", "Alice"])
        execute_command(["SET", "user:2", "Bob"])
        execute_command(["SET", "user:3", "Charlie"])

        # Get them back
        assert execute_command(["GET", "user:1"]) == "Alice"
        assert execute_command(["GET", "user:2"]) == "Bob"
        assert execute_command(["GET", "user:3"]) == "Charlie"

    def test_empty_value(self):
        """SET and GET empty string."""
        execute_command(["SET", "empty", ""])
        result = execute_command(["GET", "empty"])

        assert result == ""

        # Encode and verify
        response = RESPEncoder.encode(result)
        assert response == b"$0\r\n\r\n"

    def test_storage_isolation_between_tests(self):
        """Verify storage is clean between tests."""
        # This test verifies the fixture is working
        storage = get_storage()
        assert len(storage) == 0  # Should be empty due to fixture

        # Add something
        execute_command(["SET", "test", "value"])
        assert len(storage) == 1

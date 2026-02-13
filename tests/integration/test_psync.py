"""Integration tests for PSYNC command."""

import pytest

from app.config import Role, ServerConfig
from app.rdb import EMPTY_RDB
from app.resp import RESPEncoder
from tests.helpers import execute_command


@pytest.fixture(autouse=True)
def reset_config():
    """Reset server config before and after each test."""
    ServerConfig.reset()
    # Initialize as master
    ServerConfig.initialize(role=Role.MASTER, listening_port=6379)
    yield
    ServerConfig.reset()


class TestPsyncIntegration:
    """Integration tests for PSYNC command."""

    def test_psync_fullresync_response(self):
        """Test PSYNC returns FULLRESYNC with replication ID."""
        result = execute_command(["PSYNC", "?", "-1"])

        # Should return fullresync dict with RDB data
        repl_id = ServerConfig.get_replication_config().master_replid
        assert "fullresync" in result
        assert result["fullresync"]["replid"] == repl_id
        assert result["fullresync"]["offset"] == 0
        assert result["fullresync"]["rdb"] == EMPTY_RDB

    def test_psync_uses_master_replication_id(self):
        """Test PSYNC uses the configured master replication ID."""
        result = execute_command(["PSYNC", "?", "-1"])

        # Check fullresync dict structure
        repl_id = ServerConfig.get_replication_config().master_replid
        assert "fullresync" in result
        assert result["fullresync"]["replid"] == repl_id
        assert result["fullresync"]["offset"] == 0

    def test_psync_with_different_arguments(self):
        """Test PSYNC with different replication ID and offset."""
        # Should still return FULLRESYNC regardless of arguments (for now)
        result = execute_command(["PSYNC", "some-id", "100"])

        repl_id = ServerConfig.get_replication_config().master_replid
        assert "fullresync" in result
        assert result["fullresync"]["replid"] == repl_id

    def test_psync_no_arguments_error(self):
        """Test PSYNC without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["PSYNC"])

    def test_psync_one_argument_error(self):
        """Test PSYNC with only one argument raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["PSYNC", "?"])

    def test_psync_too_many_arguments_error(self):
        """Test PSYNC with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["PSYNC", "?", "-1", "extra"])

    def test_psync_resp_encoding(self):
        """Test PSYNC RESP encoding format."""
        encoded = RESPEncoder.encode(["PSYNC", "?", "-1"])

        # Verify exact RESP format
        assert encoded == b"*3\r\n$5\r\nPSYNC\r\n$1\r\n?\r\n$2\r\n-1\r\n"

        # Verify components
        assert encoded.startswith(b"*3\r\n")  # Array with 3 elements
        assert b"$5\r\nPSYNC\r\n" in encoded  # Command
        assert b"$1\r\n?\r\n" in encoded  # Replication ID
        assert b"$2\r\n-1\r\n" in encoded  # Offset

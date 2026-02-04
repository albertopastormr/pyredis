"""Unit tests for PSYNC command."""

import asyncio
from unittest.mock import patch

import pytest

from app.commands.psync import PsyncCommand
from app.config import ReplicationConfig, Role
from app.rdb import EMPTY_RDB


@pytest.fixture
def psync_cmd():
    """Fixture providing a PsyncCommand instance."""
    return PsyncCommand()


class TestPsyncCommand:
    """Test PSYNC command implementation."""

    def test_name(self, psync_cmd):
        """Command name is 'PSYNC'."""
        assert psync_cmd.name == "PSYNC"

    @patch("app.commands.psync.ServerConfig.get_replication_config")
    def test_psync_fullresync(self, mock_get_config, psync_cmd):
        """PSYNC returns FULLRESYNC with replication ID and offset."""
        mock_get_config.return_value = ReplicationConfig(
            role=Role.MASTER,
            master_replid="8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb",
            master_repl_offset=0
        )
        
        result = asyncio.run(psync_cmd.execute(["?", "-1"]))
        
        # Should return fullresync dict with RDB data
        assert "fullresync" in result
        assert result["fullresync"]["replid"] == "8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb"
        assert result["fullresync"]["offset"] == 0
        assert result["fullresync"]["rdb"] == EMPTY_RDB

    @patch("app.commands.psync.ServerConfig.get_replication_config")
    def test_psync_uses_replication_id(self, mock_get_config, psync_cmd):
        """PSYNC uses the master's replication ID from ServerConfig."""
        # Test with different replication ID
        mock_get_config.return_value = ReplicationConfig(
            role=Role.MASTER,
            master_replid="abc123def456",
            master_repl_offset=100
        )
        
        result = asyncio.run(psync_cmd.execute(["?", "-1"]))
        
        # Check fullresync response structure
        assert "fullresync" in result
        assert result["fullresync"]["replid"] == "abc123def456"
        assert result["fullresync"]["offset"] == 100

    def test_psync_requires_two_args(self, psync_cmd):
        """PSYNC requires exactly 2 arguments."""
        # Test with no arguments
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(psync_cmd.execute([]))
        
        # Test with one argument
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(psync_cmd.execute(["?"]))
        
        # Test with too many arguments
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(psync_cmd.execute(["?", "-1", "extra"]))

    @patch("app.commands.psync.ServerConfig.get_replication_config")
    def test_psync_accepts_any_arguments(self, mock_get_config, psync_cmd):
        """PSYNC accepts any replication ID and offset (not just ? -1)."""
        mock_get_config.return_value = ReplicationConfig(
            role=Role.MASTER,
            master_replid="test123",
            master_repl_offset=0
        )
        
        result = asyncio.run(psync_cmd.execute(["some-repl-id", "123"]))
        
        
        # Always returns FULLRESYNC for now
        assert "fullresync" in result
        assert result["fullresync"]["replid"] == "test123"
        assert result["fullresync"]["offset"] == 0
        assert result["fullresync"]["rdb"] == EMPTY_RDB

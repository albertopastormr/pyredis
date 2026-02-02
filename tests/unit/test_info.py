"""Unit tests for INFO command."""

import asyncio
from unittest.mock import patch

import pytest

from app.commands.info import InfoCommand
from app.config import ReplicationConfig, Role


@pytest.fixture
def info_command():
    """Fixture providing an INFO command instance."""
    return InfoCommand()


class TestInfoCommand:
    """Test INFO command in isolation."""

    @patch("app.commands.info.ServerConfig.get_replication_config")
    def test_info_replication_master_role(self, mock_get_config, info_command):
        """INFO replication returns master role when configured as master."""
        mock_get_config.return_value = ReplicationConfig(role=Role.MASTER)

        result = asyncio.run(info_command.execute(["replication"]))

        assert isinstance(result, str)
        assert "# Replication" in result
        assert "role:master" in result
        assert "master_replid:8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb" in result
        assert "master_repl_offset:0" in result

    @patch("app.commands.info.ServerConfig.get_replication_config")
    def test_info_replication_slave_role(self, mock_get_config, info_command):
        """INFO replication returns slave role when configured as replica."""
        mock_get_config.return_value = ReplicationConfig(
            role=Role.SLAVE,
            master_host="localhost",
            master_port=6379,
        )

        result = asyncio.run(info_command.execute(["replication"]))

        assert isinstance(result, str)
        assert "# Replication" in result
        assert "role:slave" in result

    @patch("app.commands.info.ServerConfig.get_replication_config")
    def test_info_no_args_returns_replication(self, mock_get_config, info_command):
        """INFO without args defaults to replication section."""
        mock_get_config.return_value = ReplicationConfig(role=Role.MASTER)

        result = asyncio.run(info_command.execute([]))

        assert isinstance(result, str)
        assert "# Replication" in result
        assert "role:master" in result

    @patch("app.commands.info.ServerConfig.get_replication_config")
    def test_info_case_insensitive(self, mock_get_config, info_command):
        """INFO section parameter is case-insensitive."""
        mock_get_config.return_value = ReplicationConfig(role=Role.MASTER)

        result_lower = asyncio.run(info_command.execute(["replication"]))
        result_upper = asyncio.run(info_command.execute(["REPLICATION"]))
        result_mixed = asyncio.run(info_command.execute(["RePLiCaTion"]))

        assert result_lower == result_upper == result_mixed

    def test_info_unsupported_section(self, info_command):
        """INFO with unsupported section returns empty string."""
        result = asyncio.run(info_command.execute(["memory"]))
        assert result == ""

        result = asyncio.run(info_command.execute(["server"]))
        assert result == ""

    def test_info_too_many_args(self, info_command):
        """INFO with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(info_command.execute(["replication", "extra"]))

    def test_command_name(self, info_command):
        """Command has correct name."""
        assert info_command.name == "INFO"

    @patch("app.commands.info.ServerConfig.get_replication_config")
    def test_info_format(self, mock_get_config, info_command):
        """INFO response has correct format with newlines."""
        mock_get_config.return_value = ReplicationConfig(role=Role.MASTER)
        
        result = asyncio.run(info_command.execute(["replication"]))

        lines = result.split("\n")
        assert len(lines) == 4
        assert lines[0] == "# Replication"
        assert lines[1] == "role:master"
        assert lines[2] == "master_replid:8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb"
        assert lines[3] == "master_repl_offset:0"

    def test_info_bypasses_transaction_queue(self, info_command):
        """INFO command does not bypass transaction queue by default."""
        assert info_command.bypasses_transaction_queue is False

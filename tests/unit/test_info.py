"""Unit tests for INFO command."""

import asyncio

import pytest

from app.commands.info import InfoCommand


@pytest.fixture
def info_command():
    """Fixture providing an INFO command instance."""
    return InfoCommand()


class TestInfoCommand:
    """Test INFO command in isolation."""

    def test_info_replication_section(self, info_command):
        """INFO replication returns replication section."""
        result = asyncio.run(info_command.execute(["replication"]))

        assert isinstance(result, str)
        assert "# Replication" in result
        assert "role:master" in result

    def test_info_no_args_returns_replication(self, info_command):
        """INFO without args defaults to replication section."""
        result = asyncio.run(info_command.execute([]))

        assert isinstance(result, str)
        assert "# Replication" in result
        assert "role:master" in result

    def test_info_case_insensitive(self, info_command):
        """INFO section parameter is case-insensitive."""
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

    def test_info_format(self, info_command):
        """INFO response has correct format with newlines."""
        result = asyncio.run(info_command.execute(["replication"]))

        lines = result.split("\n")
        assert len(lines) == 2
        assert lines[0] == "# Replication"
        assert lines[1] == "role:master"

    def test_info_bypasses_transaction_queue(self, info_command):
        """INFO command does not bypass transaction queue by default."""
        assert info_command.bypasses_transaction_queue is False

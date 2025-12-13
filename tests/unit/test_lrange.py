"""Unit tests for LRANGE command (with mocked storage)."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from app.commands.lrange import LrangeCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def lrange_command():
    """Fixture providing an LRANGE command instance."""
    return LrangeCommand()


class TestLrangeCommand:
    """Test LRANGE command in isolation with mocked storage."""

    @patch("app.commands.lrange.get_storage")
    def test_lrange_returns_list(self, mock_get_storage, lrange_command, mock_storage):
        """LRANGE returns list from storage."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lrange.return_value = ["a", "b", "c"]

        result = asyncio.run(lrange_command.execute(["mylist", "0", "2"]))

        mock_storage.lrange.assert_called_once_with("mylist", 0, 2)
        assert result == ["a", "b", "c"]

    @patch("app.commands.lrange.get_storage")
    def test_lrange_empty_list(self, mock_get_storage, lrange_command, mock_storage):
        """LRANGE can return empty list."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lrange.return_value = []

        result = asyncio.run(lrange_command.execute(["nonexistent", "0", "5"]))

        mock_storage.lrange.assert_called_once_with("nonexistent", 0, 5)
        assert result == []

    @patch("app.commands.lrange.get_storage")
    def test_lrange_converts_indices_to_int(self, mock_get_storage, lrange_command, mock_storage):
        """LRANGE converts string indices to integers."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lrange.return_value = ["x", "y"]

        asyncio.run(lrange_command.execute(["list", "10", "20"]))
        # Verify integers were passed to storage
        mock_storage.lrange.assert_called_once_with("list", 10, 20)

    def test_lrange_no_args(self, lrange_command):
        """LRANGE without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(lrange_command.execute([]))

    def test_lrange_one_arg(self, lrange_command):
        """LRANGE with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(lrange_command.execute(["key"]))

    def test_lrange_two_args(self, lrange_command):
        """LRANGE with only key and start raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(lrange_command.execute(["key", "0"]))

    def test_lrange_too_many_args(self, lrange_command):
        """LRANGE with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(lrange_command.execute(["key", "0", "5", "extra"]))

    def test_lrange_invalid_start(self, lrange_command):
        """LRANGE with non-integer start raises error."""
        with pytest.raises(ValueError, match="not an integer"):
            asyncio.run(lrange_command.execute(["key", "abc", "5"]))

    def test_lrange_invalid_stop(self, lrange_command):
        """LRANGE with non-integer stop raises error."""
        with pytest.raises(ValueError, match="not an integer"):
            asyncio.run(lrange_command.execute(["key", "0", "xyz"]))

    def test_command_name(self, lrange_command):
        """Command has correct name."""
        assert lrange_command.name == "LRANGE"

    @patch("app.commands.lrange.get_storage")
    def test_lrange_storage_called_once(self, mock_get_storage, lrange_command, mock_storage):
        """Verify get_storage() is called once per execute."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lrange.return_value = []

        asyncio.run(lrange_command.execute(["key", "0", "5"]))
        mock_get_storage.assert_called_once()

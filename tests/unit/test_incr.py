"""Unit tests for INCR command (with mocked storage)."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from app.commands.incr import IncrCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def incr_command():
    """Fixture providing an INCR command instance."""
    return IncrCommand()


class TestIncrCommand:
    """Test INCR command in isolation with mocked storage."""

    @patch("app.commands.incr.get_storage")
    def test_incr_increments_value(self, mock_get_storage, incr_command, mock_storage):
        """INCR command increments an existing integer value."""
        mock_get_storage.return_value = mock_storage
        mock_storage.incr.return_value = 6

        result = asyncio.run(incr_command.execute(["mykey"]))

        mock_storage.incr.assert_called_once_with("mykey")
        assert result == 6

    @patch("app.commands.incr.get_storage")
    def test_incr_nonexistent_key(self, mock_get_storage, incr_command, mock_storage):
        """INCR command sets nonexistent key to 1."""
        mock_get_storage.return_value = mock_storage
        mock_storage.incr.return_value = 1

        result = asyncio.run(incr_command.execute(["newkey"]))

        mock_storage.incr.assert_called_once_with("newkey")
        assert result == 1

    @patch("app.commands.incr.get_storage")
    def test_incr_negative_value(self, mock_get_storage, incr_command, mock_storage):
        """INCR command can increment negative values."""
        mock_get_storage.return_value = mock_storage
        mock_storage.incr.return_value = -4

        result = asyncio.run(incr_command.execute(["negkey"]))

        assert result == -4

    @patch("app.commands.incr.get_storage")
    def test_incr_zero_value(self, mock_get_storage, incr_command, mock_storage):
        """INCR command increments zero to one."""
        mock_get_storage.return_value = mock_storage
        mock_storage.incr.return_value = 1

        result = asyncio.run(incr_command.execute(["zerokey"]))

        assert result == 1

    @patch("app.commands.incr.get_storage")
    def test_incr_string_value_error(self, mock_get_storage, incr_command, mock_storage):
        """INCR command raises error for non-integer value."""
        mock_get_storage.return_value = mock_storage
        mock_storage.incr.side_effect = ValueError("value is not an integer or out of range")

        with pytest.raises(ValueError, match="ERR value is not an integer or out of range"):
            asyncio.run(incr_command.execute(["stringkey"]))

    @patch("app.commands.incr.get_storage")
    def test_incr_calls_storage_once(self, mock_get_storage, incr_command, mock_storage):
        """INCR calls storage.incr() exactly once."""
        mock_get_storage.return_value = mock_storage
        mock_storage.incr.return_value = 10

        asyncio.run(incr_command.execute(["key"]))
        mock_get_storage.assert_called_once()
        mock_storage.incr.assert_called_once_with("key")

    def test_incr_no_args(self, incr_command):
        """INCR without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(incr_command.execute([]))

    def test_incr_too_many_args(self, incr_command):
        """INCR with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(incr_command.execute(["key", "extra"]))

    def test_command_name(self, incr_command):
        """Command has correct name."""
        assert incr_command.name == "INCR"

    @patch("app.commands.incr.get_storage")
    def test_incr_handles_storage_exception(self, mock_get_storage, incr_command, mock_storage):
        """INCR wraps storage exceptions properly."""
        mock_get_storage.return_value = mock_storage
        mock_storage.incr.side_effect = RuntimeError("Storage error")

        with pytest.raises(ValueError, match="ERR"):
            asyncio.run(incr_command.execute(["key"]))

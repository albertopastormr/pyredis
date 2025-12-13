"""Unit tests for LPOP command (with mocked storage)."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from app.commands.lpop import LpopCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def lpop_command():
    """Fixture providing an LPOP command instance."""
    return LpopCommand()


class TestLpopCommand:
    """Test LPOP command in isolation with mocked storage."""

    @patch("app.commands.lpop.get_storage")
    def test_lpop_single_element(self, mock_get_storage, lpop_command, mock_storage):
        """LPOP returns single element when no count specified."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpop.return_value = ["a"]

        result = asyncio.run(lpop_command.execute(["mylist"]))

        mock_storage.lpop.assert_called_once_with("mylist", 1)
        assert result == "a"

    @patch("app.commands.lpop.get_storage")
    def test_lpop_multiple_elements(self, mock_get_storage, lpop_command, mock_storage):
        """LPOP returns array when count specified."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpop.return_value = ["a", "b", "c"]

        result = asyncio.run(lpop_command.execute(["mylist", "3"]))

        mock_storage.lpop.assert_called_once_with("mylist", 3)
        assert result == ["a", "b", "c"]

    @patch("app.commands.lpop.get_storage")
    def test_lpop_returns_none_for_nonexistent(self, mock_get_storage, lpop_command, mock_storage):
        """LPOP returns None for non-existent key."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpop.return_value = None

        result = asyncio.run(lpop_command.execute(["nonexistent"]))

        assert result is None

    @patch("app.commands.lpop.get_storage")
    def test_lpop_empty_result_with_count(self, mock_get_storage, lpop_command, mock_storage):
        """LPOP returns empty list when result is empty with count."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpop.return_value = []

        result = asyncio.run(lpop_command.execute(["mylist", "5"]))

        assert result == []

    def test_lpop_no_args(self, lpop_command):
        """LPOP without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(lpop_command.execute([]))

    def test_lpop_too_many_args(self, lpop_command):
        """LPOP with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(lpop_command.execute(["key", "1", "extra"]))

    def test_lpop_invalid_count(self, lpop_command):
        """LPOP with non-integer count raises error."""
        with pytest.raises(ValueError, match="not an integer"):
            asyncio.run(lpop_command.execute(["key", "abc"]))

    def test_lpop_negative_count(self, lpop_command):
        """LPOP with negative count raises error."""
        with pytest.raises(ValueError, match="out of range"):
            asyncio.run(lpop_command.execute(["key", "-1"]))

    def test_command_name(self, lpop_command):
        """Command has correct name."""
        assert lpop_command.name == "LPOP"

    @patch("app.commands.lpop.get_storage")
    def test_lpop_storage_called_once(self, mock_get_storage, lpop_command, mock_storage):
        """Verify get_storage() is called once per execute."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpop.return_value = ["a"]

        asyncio.run(lpop_command.execute(["key"]))
        mock_get_storage.assert_called_once()

"""Unit tests for XINFO command (with mocked storage)."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from app.commands.xinfo import XinfoCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def xinfo_command():
    """Fixture providing an XINFO command instance."""
    return XinfoCommand()


class TestXinfoCommand:
    """Test XINFO command in isolation with mocked storage."""

    @patch("app.commands.xinfo.get_storage")
    def test_xinfo_basic(self, mock_get_storage, xinfo_command, mock_storage):
        """XINFO STREAM returns correct metadata."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xinfo.return_value = {
            "length": 1,
            "last-generated-id": "1-0",
            "first-entry": ("1-0", {"a": "1"}),
            "last-entry": ("1-0", {"a": "1"}),
        }

        result = asyncio.run(xinfo_command.execute(["STREAM", "mystream"]))

        mock_storage.xinfo.assert_called_once_with("mystream")

        # Verify result is a flat list with correct fields
        assert "length" in result
        assert result[result.index("length") + 1] == 1
        assert "last-generated-id" in result
        assert result[result.index("last-generated-id") + 1] == "1-0"

    @patch("app.commands.xinfo.get_storage")
    def test_xinfo_empty_stream(self, mock_get_storage, xinfo_command, mock_storage):
        """XINFO STREAM handles empty stream."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xinfo.return_value = {
            "length": 0,
            "last-generated-id": "0-0",
            "first-entry": None,
            "last-entry": None,
        }

        result = asyncio.run(xinfo_command.execute(["STREAM", "empty"]))

        assert result[result.index("length") + 1] == 0
        assert result[result.index("last-generated-id") + 1] == "0-0"
        assert result[result.index("first-entry") + 1] is None
        assert result[result.index("last-entry") + 1] is None

    @patch("app.commands.xinfo.get_storage")
    def test_xinfo_missing_fields_in_dict(self, mock_get_storage, xinfo_command, mock_storage):
        """XINFO STREAM handles missing optional fields in storage return."""
        mock_get_storage.return_value = mock_storage
        # storage returns minimal dict
        mock_storage.xinfo.return_value = {
            "length": 5
            # Missing last-generated-id, first-entry, last-entry
        }

        result = asyncio.run(xinfo_command.execute(["STREAM", "partial"]))

        assert result[result.index("length") + 1] == 5
        assert result[result.index("last-generated-id") + 1] == "0-0"  # Default
        assert result[result.index("first-entry") + 1] is None
        assert result[result.index("last-entry") + 1] is None

    @patch("app.commands.xinfo.get_storage")
    def test_xinfo_nonexistent_key(self, mock_get_storage, xinfo_command, mock_storage):
        """XINFO STREAM raises error for nonexistent key."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xinfo.return_value = None

        with pytest.raises(ValueError, match="no such key"):
            asyncio.run(xinfo_command.execute(["STREAM", "missing"]))

    @patch("app.commands.xinfo.get_storage")
    def test_xinfo_wrong_subcommand(self, mock_get_storage, xinfo_command, mock_storage):
        """XINFO with unknown subcommand raises error."""
        with pytest.raises(ValueError, match="unknown subcommand"):
            asyncio.run(xinfo_command.execute(["GROUPS", "key"]))

    def test_xinfo_missing_args(self, xinfo_command):
        """XINFO with missing args raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(xinfo_command.execute(["STREAM"]))

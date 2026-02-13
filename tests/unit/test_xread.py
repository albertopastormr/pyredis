"""Unit tests for XREAD command (with mocked storage)."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from app.commands.xread import XreadCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def xread_command():
    """Fixture providing an XREAD command instance."""
    return XreadCommand()


class TestXreadCommand:
    """Test XREAD command in isolation with mocked storage."""

    @patch("app.commands.xread.get_storage")
    def test_xread_single_stream(self, mock_get_storage, xread_command, mock_storage):
        """XREAD returns entries for a single stream."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xread.return_value = [("mystream", [("1-1", {"field": "value"})])]

        result = asyncio.run(xread_command.execute(["STREAMS", "mystream", "1-0"]))

        mock_storage.xread.assert_called_once_with([("mystream", "1-0")])
        assert result == [["mystream", [["1-1", ["field", "value"]]]]]

    @patch("app.commands.xread.get_storage")
    def test_xread_multiple_streams(self, mock_get_storage, xread_command, mock_storage):
        """XREAD returns entries for multiple streams."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xread.return_value = [
            ("stream1", [("1-1", {"a": "1"})]),
            ("stream2", [("2-1", {"b": "2"})]),
        ]

        result = asyncio.run(xread_command.execute(["STREAMS", "stream1", "stream2", "1-0", "2-0"]))

        mock_storage.xread.assert_called_once_with([("stream1", "1-0"), ("stream2", "2-0")])
        assert len(result) == 2
        assert result[0][0] == "stream1"
        assert result[1][0] == "stream2"

    @patch("app.commands.xread.get_storage")
    def test_xread_no_entries(self, mock_get_storage, xread_command, mock_storage):
        """XREAD returns None when no entries found."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xread.return_value = []

        result = asyncio.run(xread_command.execute(["STREAMS", "mystream", "1-0"]))

        assert result is None

    @patch("app.commands.xread.get_storage")
    def test_xread_multiple_fields(self, mock_get_storage, xread_command, mock_storage):
        """XREAD formats multiple fields correctly."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xread.return_value = [("mystream", [("1-1", {"a": "1", "b": "2", "c": "3"})])]

        result = asyncio.run(xread_command.execute(["STREAMS", "mystream", "0-0"]))

        # Fields should be flattened
        assert len(result[0][1][0][1]) == 6  # 3 field-value pairs = 6 items

    def test_xread_no_args(self, xread_command):
        """XREAD without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(xread_command.execute([]))

    def test_xread_missing_streams_keyword(self, xread_command):
        """XREAD without STREAMS keyword raises error."""
        with pytest.raises(ValueError, match="syntax error"):
            asyncio.run(xread_command.execute(["mystream", "0-0"]))

    def test_xread_unbalanced_keys_ids(self, xread_command):
        """XREAD with unbalanced keys/IDs raises error."""
        with pytest.raises(ValueError, match="Unbalanced"):
            asyncio.run(xread_command.execute(["STREAMS", "stream1", "stream2", "0-0"]))

    def test_xread_streams_only(self, xread_command):
        """XREAD with only STREAMS keyword raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(xread_command.execute(["STREAMS"]))

    def test_command_name(self, xread_command):
        """Command has correct name."""
        assert xread_command.name == "XREAD"

    @patch("app.commands.xread.get_storage")
    def test_xread_case_insensitive_streams(self, mock_get_storage, xread_command, mock_storage):
        """STREAMS keyword is case-insensitive."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xread.return_value = []

        # Should not raise - lowercase 'streams' should work
        asyncio.run(xread_command.execute(["streams", "mystream", "0-0"]))
        mock_storage.xread.assert_called_once()


class TestXreadBlockParsing:
    """Test XREAD BLOCK argument parsing."""

    @pytest.fixture
    def xread_command(self):
        return XreadCommand()

    @pytest.fixture
    def mock_storage(self):
        return Mock()

    @patch("app.commands.xread.get_storage")
    def test_xread_block_with_data_returns_immediately(
        self, mock_get_storage, xread_command, mock_storage
    ):
        """XREAD BLOCK returns immediately if data exists."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xread.return_value = [("mystream", [("1-1", {"field": "value"})])]

        result = asyncio.run(xread_command.execute(["BLOCK", "1000", "STREAMS", "mystream", "0-0"]))

        assert result == [["mystream", [["1-1", ["field", "value"]]]]]

    @patch("app.commands.xread.get_storage")
    def test_xread_block_zero_with_data(self, mock_get_storage, xread_command, mock_storage):
        """XREAD BLOCK 0 returns immediately if data exists."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xread.return_value = [("mystream", [("1-1", {"a": "1"})])]

        result = asyncio.run(xread_command.execute(["BLOCK", "0", "STREAMS", "mystream", "0-0"]))

        assert result is not None

    def test_xread_block_missing_timeout(self, xread_command):
        """XREAD BLOCK without timeout raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(xread_command.execute(["BLOCK"]))

    def test_xread_block_invalid_timeout(self, xread_command):
        """XREAD BLOCK with non-integer timeout raises error."""
        with pytest.raises(ValueError, match="not an integer"):
            asyncio.run(xread_command.execute(["BLOCK", "abc", "STREAMS", "mystream", "0-0"]))

    def test_xread_block_negative_timeout(self, xread_command):
        """XREAD BLOCK with negative timeout raises error."""
        with pytest.raises(ValueError, match="negative"):
            asyncio.run(xread_command.execute(["BLOCK", "-1", "STREAMS", "mystream", "0-0"]))

    def test_xread_block_missing_streams(self, xread_command):
        """XREAD BLOCK without STREAMS keyword raises error."""
        with pytest.raises(ValueError, match="syntax error"):
            asyncio.run(xread_command.execute(["BLOCK", "1000", "mystream", "0-0"]))

    @patch("app.commands.xread.get_storage")
    def test_xread_block_case_insensitive(self, mock_get_storage, xread_command, mock_storage):
        """BLOCK keyword is case-insensitive."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xread.return_value = [("mystream", [("1-1", {"a": "1"})])]

        result = asyncio.run(xread_command.execute(["block", "1000", "streams", "mystream", "0-0"]))

        assert result is not None

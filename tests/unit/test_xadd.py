"""Unit tests for XADD command (with mocked storage)."""

import asyncio
from unittest.mock import Mock, patch

import pytest

from app.commands.xadd import XaddCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def xadd_command():
    """Fixture providing an XADD command instance."""
    return XaddCommand()


class TestXaddCommand:
    """Test XADD command in isolation with mocked storage."""

    @patch("app.commands.xadd.get_storage")
    def test_xadd_returns_entry_id(self, mock_get_storage, xadd_command, mock_storage):
        """XADD returns the entry ID."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xadd.return_value = "1526985054069-0"

        result = asyncio.run(
            xadd_command.execute(["mystream", "1526985054069-0", "temperature", "36"])
        )

        mock_storage.xadd.assert_called_once_with(
            "mystream", "1526985054069-0", {"temperature": "36"}
        )
        assert result == "1526985054069-0"

    @patch("app.commands.xadd.get_storage")
    def test_xadd_single_field(self, mock_get_storage, xadd_command, mock_storage):
        """XADD with single field-value pair."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xadd.return_value = "0-1"

        result = asyncio.run(xadd_command.execute(["stream", "0-1", "foo", "bar"]))

        mock_storage.xadd.assert_called_once_with("stream", "0-1", {"foo": "bar"})
        assert result == "0-1"

    @patch("app.commands.xadd.get_storage")
    def test_xadd_multiple_fields(self, mock_get_storage, xadd_command, mock_storage):
        """XADD with multiple field-value pairs."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xadd.return_value = "1526985054079-0"

        result = asyncio.run(
            xadd_command.execute(
                [
                    "weather",
                    "1526985054079-0",
                    "temperature",
                    "37",
                    "humidity",
                    "94",
                ]
            )
        )

        mock_storage.xadd.assert_called_once_with(
            "weather", "1526985054079-0", {"temperature": "37", "humidity": "94"}
        )
        assert result == "1526985054079-0"

    @patch("app.commands.xadd.get_storage")
    def test_xadd_empty_field_value(self, mock_get_storage, xadd_command, mock_storage):
        """XADD handles empty string values."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xadd.return_value = "0-1"

        asyncio.run(xadd_command.execute(["stream", "0-1", "field", ""]))

        mock_storage.xadd.assert_called_once_with("stream", "0-1", {"field": ""})

    def test_xadd_no_args(self, xadd_command):
        """XADD without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(xadd_command.execute([]))

    def test_xadd_missing_fields(self, xadd_command):
        """XADD with only key and ID raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(xadd_command.execute(["key", "0-1"]))

    def test_xadd_missing_value(self, xadd_command):
        """XADD with odd number of field-value pairs raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(xadd_command.execute(["key", "0-1", "field"]))

    def test_xadd_odd_field_values(self, xadd_command):
        """XADD with odd field-value count raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(xadd_command.execute(["key", "0-1", "f1", "v1", "f2", "v2", "f3"]))

    def test_command_name(self, xadd_command):
        """Command has correct name."""
        assert xadd_command.name == "XADD"

    @patch("app.commands.xadd.get_storage")
    def test_xadd_storage_called_once(self, mock_get_storage, xadd_command, mock_storage):
        """Verify get_storage() is called once per execute."""
        mock_get_storage.return_value = mock_storage
        mock_storage.xadd.return_value = "0-1"

        asyncio.run(xadd_command.execute(["key", "0-1", "field", "value"]))
        mock_get_storage.assert_called_once()

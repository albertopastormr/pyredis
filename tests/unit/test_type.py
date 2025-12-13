"""Unit tests for TYPE command."""

import asyncio

import pytest

from app.commands.type import TypeCommand


class MockStorage:
    """Mock storage for testing."""

    def __init__(self, type_result):
        self.type_result = type_result
        self.type_called_with = None

    def type(self, key):
        self.type_called_with = key
        return self.type_result


class TestTypeCommand:
    """Test TYPE command implementation."""

    def test_type_returns_string_for_string_value(self, monkeypatch):
        """TYPE returns 'string' for string values."""
        type_command = TypeCommand()
        mock_storage = MockStorage("string")
        monkeypatch.setattr("app.commands.type.get_storage", lambda: mock_storage)

        result = asyncio.run(type_command.execute(["mykey"]))

        assert result == {"ok": "string"}
        assert mock_storage.type_called_with == "mykey"

    def test_type_returns_list_for_list_value(self, monkeypatch):
        """TYPE returns 'list' for list values."""
        type_command = TypeCommand()
        mock_storage = MockStorage("list")
        monkeypatch.setattr("app.commands.type.get_storage", lambda: mock_storage)

        result = asyncio.run(type_command.execute(["mylist"]))

        assert result == {"ok": "list"}
        assert mock_storage.type_called_with == "mylist"

    def test_type_returns_none_for_nonexistent_key(self, monkeypatch):
        """TYPE returns 'none' for non-existent keys."""
        type_command = TypeCommand()
        mock_storage = MockStorage("none")
        monkeypatch.setattr("app.commands.type.get_storage", lambda: mock_storage)

        result = asyncio.run(type_command.execute(["nonexistent"]))

        assert result == {"ok": "none"}
        assert mock_storage.type_called_with == "nonexistent"

    def test_type_no_args(self):
        """TYPE without arguments raises error."""
        type_command = TypeCommand()

        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(type_command.execute([]))

    def test_type_too_many_args(self):
        """TYPE with too many arguments raises error."""
        type_command = TypeCommand()

        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(type_command.execute(["key1", "key2"]))

    def test_command_name(self):
        """TYPE command has correct name."""
        type_command = TypeCommand()
        assert type_command.name == "TYPE"

    def test_type_storage_called_once(self, monkeypatch):
        """TYPE calls storage.type exactly once."""
        type_command = TypeCommand()
        mock_storage = MockStorage("string")
        monkeypatch.setattr("app.commands.type.get_storage", lambda: mock_storage)

        asyncio.run(type_command.execute(["key"]))

        assert mock_storage.type_called_with == "key"

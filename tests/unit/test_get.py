"""Unit tests for GET command (with mocked storage)."""

import pytest
import asyncio
from unittest.mock import Mock, patch

from app.commands.get import GetCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def get_command():
    """Fixture providing a GET command instance."""
    return GetCommand()


class TestGetCommand:
    """Test GET command in isolation with mocked storage."""
    
    @patch('app.commands.get.get_storage')
    def test_get_returns_value_from_storage(self, mock_get_storage, get_command, mock_storage):
        """GET command returns value from storage.get()."""
        mock_get_storage.return_value = mock_storage
        mock_storage.get.return_value = 'myvalue'
        
        result = asyncio.run(get_command.execute(['mykey']))
        
        mock_storage.get.assert_called_once_with('mykey')
        assert result == 'myvalue'
    
    @patch('app.commands.get.get_storage')
    def test_get_returns_none_for_missing_key(self, mock_get_storage, get_command, mock_storage):
        """GET command returns None when storage returns None."""
        mock_get_storage.return_value = mock_storage
        mock_storage.get.return_value = None
        
        result = asyncio.run(get_command.execute(['nonexistent']))
        
        mock_storage.get.assert_called_once_with('nonexistent')
        assert result is None
    
    @patch('app.commands.get.get_storage')
    def test_get_empty_value(self, mock_get_storage, get_command, mock_storage):
        """GET command can return empty string."""
        mock_get_storage.return_value = mock_storage
        mock_storage.get.return_value = ''
        
        result = asyncio.run(get_command.execute(['key']))
        
        assert result == ''
    
    @patch('app.commands.get.get_storage')
    def test_get_special_characters(self, mock_get_storage, get_command, mock_storage):
        """GET command handles special characters."""
        mock_get_storage.return_value = mock_storage
        special_value = 'hello\r\n\t世界'
        mock_storage.get.return_value = special_value
        
        result = asyncio.run(get_command.execute(['key']))
        
        assert result == special_value
    
    @patch('app.commands.get.get_storage')
    def test_get_calls_storage_once(self, mock_get_storage, get_command, mock_storage):
        """GET calls storage.get() exactly once."""
        mock_get_storage.return_value = mock_storage
        mock_storage.get.return_value = 'value'
        
        asyncio.run(get_command.execute(['key']))
        mock_get_storage.assert_called_once()
        mock_storage.get.assert_called_once_with('key')
    
    def test_get_no_args(self, get_command):
        """GET without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(get_command.execute([]))
    def test_get_too_many_args(self, get_command):
        """GET with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(get_command.execute(['key', 'extra']))
    def test_command_name(self, get_command):
        """Command has correct name."""
        assert get_command.name == 'GET'
    
    @patch('app.commands.get.get_storage')
    def test_get_handles_storage_exception(self, mock_get_storage, get_command, mock_storage):
        """GET wraps storage exceptions properly."""
        mock_get_storage.return_value = mock_storage
        mock_storage.get.side_effect = RuntimeError("Storage error")
        
        with pytest.raises(ValueError, match="ERR"):
            asyncio.run(get_command.execute(['key']))
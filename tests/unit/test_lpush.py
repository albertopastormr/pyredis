"""Unit tests for LPUSH command (with mocked storage)."""

import pytest
import asyncio
from unittest.mock import Mock, patch

from app.commands.lpush import LpushCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def lpush_command():
    """Fixture providing an LPUSH command instance."""
    return LpushCommand()


class TestLpushCommand:
    """Test LPUSH command in isolation with mocked storage."""
    
    @patch('app.commands.lpush.get_storage')
    def test_lpush_returns_length(self, mock_get_storage, lpush_command, mock_storage):
        """LPUSH returns list length."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpush.return_value = 3
        
        result = asyncio.run(lpush_command.execute(['mylist', 'value']))
        
        mock_storage.lpush.assert_called_once_with('mylist', 'value')
        assert result == 3
    
    @patch('app.commands.lpush.get_storage')
    def test_lpush_single_value(self, mock_get_storage, lpush_command, mock_storage):
        """LPUSH with single value."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpush.return_value = 1
        
        result = asyncio.run(lpush_command.execute(['list', 'foo']))
        
        mock_storage.lpush.assert_called_once_with('list', 'foo')
        assert result == 1
    
    @patch('app.commands.lpush.get_storage')
    def test_lpush_multiple_values(self, mock_get_storage, lpush_command, mock_storage):
        """LPUSH with multiple values."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpush.return_value = 5
        
        result = asyncio.run(lpush_command.execute(['list', 'foo', 'bar', 'baz']))
        
        mock_storage.lpush.assert_called_once_with('list', 'foo', 'bar', 'baz')
        assert result == 5
    
    @patch('app.commands.lpush.get_storage')
    def test_lpush_empty_value(self, mock_get_storage, lpush_command, mock_storage):
        """LPUSH handles empty string values."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpush.return_value = 1
        
        result = asyncio.run(lpush_command.execute(['list', '']))
        
        mock_storage.lpush.assert_called_once_with('list', '')
    
    def test_lpush_no_args(self, lpush_command):
        """LPUSH without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(lpush_command.execute([]))
    def test_lpush_one_arg(self, lpush_command):
        """LPUSH with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(lpush_command.execute(['key']))
    def test_command_name(self, lpush_command):
        """Command has correct name."""
        assert lpush_command.name == 'LPUSH'
    
    @patch('app.commands.lpush.get_storage')
    def test_lpush_storage_called_once(self, mock_get_storage, lpush_command, mock_storage):
        """Verify get_storage() is called once per execute."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpush.return_value = 1
        
        asyncio.run(lpush_command.execute(['key', 'value']))
        mock_get_storage.assert_called_once()

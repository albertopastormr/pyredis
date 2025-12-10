"""Unit tests for RPUSH command (with mocked storage)."""

import pytest
from unittest.mock import Mock, patch

from app.commands.rpush import RpushCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def rpush_command():
    """Fixture providing an RPUSH command instance."""
    return RpushCommand()


class TestRpushCommand:
    """Test RPUSH command in isolation with mocked storage."""
    
    @patch('app.commands.rpush.get_storage')
    def test_rpush_returns_length(self, mock_get_storage, rpush_command, mock_storage):
        """RPUSH returns list length."""
        mock_get_storage.return_value = mock_storage
        mock_storage.rpush.return_value = 3
        
        result = rpush_command.execute(['mylist', 'value'])
        
        mock_storage.rpush.assert_called_once_with('mylist', 'value')
        assert result == 3
    
    @patch('app.commands.rpush.get_storage')
    def test_rpush_single_value(self, mock_get_storage, rpush_command, mock_storage):
        """RPUSH with single value."""
        mock_get_storage.return_value = mock_storage
        mock_storage.rpush.return_value = 1
        
        result = rpush_command.execute(['list', 'foo'])
        
        mock_storage.rpush.assert_called_once_with('list', 'foo')
        assert result == 1
    
    @patch('app.commands.rpush.get_storage')
    def test_rpush_multiple_values(self, mock_get_storage, rpush_command, mock_storage):
        """RPUSH with multiple values."""
        mock_get_storage.return_value = mock_storage
        mock_storage.rpush.return_value = 5
        
        result = rpush_command.execute(['list', 'foo', 'bar', 'baz'])
        
        mock_storage.rpush.assert_called_once_with('list', 'foo', 'bar', 'baz')
        assert result == 5
    
    @patch('app.commands.rpush.get_storage')
    def test_rpush_empty_value(self, mock_get_storage, rpush_command, mock_storage):
        """RPUSH handles empty string values."""
        mock_get_storage.return_value = mock_storage
        mock_storage.rpush.return_value = 1
        
        result = rpush_command.execute(['list', ''])
        
        mock_storage.rpush.assert_called_once_with('list', '')
    
    def test_rpush_no_args(self, rpush_command):
        """RPUSH without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            rpush_command.execute([])
    
    def test_rpush_one_arg(self, rpush_command):
        """RPUSH with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            rpush_command.execute(['key'])
    
    def test_command_name(self, rpush_command):
        """Command has correct name."""
        assert rpush_command.name == 'RPUSH'
    
    @patch('app.commands.rpush.get_storage')
    def test_rpush_storage_called_once(self, mock_get_storage, rpush_command, mock_storage):
        """Verify get_storage() is called once per execute."""
        mock_get_storage.return_value = mock_storage
        mock_storage.rpush.return_value = 1
        
        rpush_command.execute(['key', 'value'])
        
        mock_get_storage.assert_called_once()

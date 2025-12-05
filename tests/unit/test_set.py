"""Unit tests for SET command (with mocked storage)."""

import pytest
from unittest.mock import Mock, patch

from app.commands.set import SetCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def set_command():
    """Fixture providing a SET command instance."""
    return SetCommand()


class TestSetCommand:
    """Test SET command in isolation with mocked storage."""
    
    @patch('app.commands.set.get_storage')
    def test_set_calls_storage_set(self, mock_get_storage, set_command, mock_storage):
        """SET command calls storage.set() with correct args."""
        mock_get_storage.return_value = mock_storage
        
        result = set_command.execute(['mykey', 'myvalue'])
        
        mock_storage.set.assert_called_once_with('mykey', 'myvalue')
        assert result == {'ok': 'OK'}
    
    @patch('app.commands.set.get_storage')
    def test_set_returns_ok(self, mock_get_storage, set_command, mock_storage):
        """SET command returns OK response."""
        mock_get_storage.return_value = mock_storage
        
        result = set_command.execute(['key', 'value'])
        
        assert result == {'ok': 'OK'}
    
    @patch('app.commands.set.get_storage')
    def test_set_with_empty_value(self, mock_get_storage, set_command, mock_storage):
        """SET command handles empty value."""
        mock_get_storage.return_value = mock_storage
        
        result = set_command.execute(['key', ''])
        
        mock_storage.set.assert_called_once_with('key', '')
        assert result == {'ok': 'OK'}
    
    @patch('app.commands.set.get_storage')
    def test_set_with_special_chars(self, mock_get_storage, set_command, mock_storage):
        """SET command handles special characters."""
        mock_get_storage.return_value = mock_storage
        special_value = 'hello\r\n\t世界'
        
        result = set_command.execute(['key', special_value])
        
        mock_storage.set.assert_called_once_with('key', special_value)
    
    def test_set_no_args(self, set_command):
        """SET without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            set_command.execute([])
    
    def test_set_one_arg(self, set_command):
        """SET with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            set_command.execute(['key'])
    
    def test_set_too_many_args(self, set_command):
        """SET with too many arguments raises error."""
        # 5 args is too many (valid is 2 or 4 with PX)
        with pytest.raises(ValueError, match="wrong number of arguments|syntax error"):
            set_command.execute(['key', 'value', 'extra', 'arg4', 'arg5'])
    
    def test_command_name(self, set_command):
        """Command has correct name."""
        assert set_command.name == 'SET'
    
    @patch('app.commands.set.get_storage')
    def test_set_storage_called_once_per_execution(self, mock_get_storage, set_command, mock_storage):
        """Verify get_storage() is called once per execute."""
        mock_get_storage.return_value = mock_storage
        
        set_command.execute(['key', 'value'])
        
        mock_get_storage.assert_called_once()

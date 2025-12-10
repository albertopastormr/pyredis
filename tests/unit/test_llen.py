"""Unit tests for LLEN command (with mocked storage)."""

import pytest
from unittest.mock import Mock, patch

from app.commands.llen import LlenCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def llen_command():
    """Fixture providing an LLEN command instance."""
    return LlenCommand()


class TestLlenCommand:
    """Test LLEN command in isolation with mocked storage."""
    
    @patch('app.commands.llen.get_storage')
    def test_llen_returns_length(self, mock_get_storage, llen_command, mock_storage):
        """LLEN returns list length from storage."""
        mock_get_storage.return_value = mock_storage
        mock_storage.llen.return_value = 5
        
        result = llen_command.execute(['mylist'])
        
        mock_storage.llen.assert_called_once_with('mylist')
        assert result == 5
    
    @patch('app.commands.llen.get_storage')
    def test_llen_returns_zero(self, mock_get_storage, llen_command, mock_storage):
        """LLEN returns 0 for non-existent list."""
        mock_get_storage.return_value = mock_storage
        mock_storage.llen.return_value = 0
        
        result = llen_command.execute(['nonexistent'])
        
        mock_storage.llen.assert_called_once_with('nonexistent')
        assert result == 0
    
    def test_llen_no_args(self, llen_command):
        """LLEN without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            llen_command.execute([])
    
    def test_llen_too_many_args(self, llen_command):
        """LLEN with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            llen_command.execute(['key', 'extra'])
    
    def test_command_name(self, llen_command):
        """Command has correct name."""
        assert llen_command.name == 'LLEN'
    
    @patch('app.commands.llen.get_storage')
    def test_llen_storage_called_once(self, mock_get_storage, llen_command, mock_storage):
        """Verify get_storage() is called once per execute."""
        mock_get_storage.return_value = mock_storage
        mock_storage.llen.return_value = 3
        
        llen_command.execute(['key'])
        
        mock_get_storage.assert_called_once()

"""Unit tests for BLPOP command (with mocked storage)."""

import pytest
from unittest.mock import Mock, patch
import time

from app.commands.blpop import BlpopCommand


@pytest.fixture
def mock_storage():
    """Fixture providing a mocked storage instance."""
    return Mock()


@pytest.fixture
def blpop_command():
    """Fixture providing a BLPOP command instance."""
    return BlpopCommand()


class TestBlpopCommand:
    """Test BLPOP command in isolation with mocked storage."""
    
    @patch('app.commands.blpop.get_storage')
    def test_blpop_immediate_return(self, mock_get_storage, blpop_command, mock_storage):
        """BLPOP returns immediately if element available."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpop.return_value = ['value']
        
        result = blpop_command.execute(['mylist', '5'])
        
        assert result == ['mylist', 'value']
    
    @patch('app.commands.blpop.get_storage')
    @patch('app.commands.blpop.time')
    def test_blpop_timeout(self, mock_time, mock_get_storage, blpop_command, mock_storage):
        """BLPOP returns None after timeout."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpop.return_value = None
        
        # Mock time to simulate timeout
        mock_time.monotonic.side_effect = [0, 0.5, 1.0, 1.5]
        mock_time.sleep.return_value = None
        
        result = blpop_command.execute(['mylist', '1'])
        
        assert result is None
    
    def test_blpop_no_args(self, blpop_command):
        """BLPOP without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            blpop_command.execute([])
    
    def test_blpop_one_arg(self, blpop_command):
        """BLPOP with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            blpop_command.execute(['key'])
    
    def test_blpop_too_many_args(self, blpop_command):
        """BLPOP with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            blpop_command.execute(['key', '1', 'extra'])
    
    def test_blpop_invalid_timeout(self, blpop_command):
        """BLPOP with non-numeric timeout raises error."""
        with pytest.raises(ValueError, match="not a float"):
            blpop_command.execute(['key', 'abc'])
    
    def test_blpop_negative_timeout(self, blpop_command):
        """BLPOP with negative timeout raises error."""
        with pytest.raises(ValueError, match="negative"):
            blpop_command.execute(['key', '-1'])
    
    def test_command_name(self, blpop_command):
        """Command has correct name."""
        assert blpop_command.name == 'BLPOP'

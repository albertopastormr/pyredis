"""Unit tests for BLPOP command (with mocked storage)."""

import pytest
import asyncio
from unittest.mock import Mock, patch

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
        
        # Run async in event loop
        result = asyncio.run(blpop_command.execute(['mylist', '5']))
        
        assert result == ['mylist', 'value']
    
    @patch('app.commands.blpop.get_storage')
    def test_blpop_timeout(self, mock_get_storage, blpop_command, mock_storage):
        """BLPOP returns None after timeout."""
        mock_get_storage.return_value = mock_storage
        mock_storage.lpop.return_value = None
        
        # Run async in event loop with short timeout
        result = asyncio.run(blpop_command.execute(['mylist', '0.1']))
        
        assert result == {'null_array': True}
    
    def test_command_name(self, blpop_command):
        """Command has correct name."""
        assert blpop_command.name == 'BLPOP'

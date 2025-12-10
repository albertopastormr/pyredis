"""Tests for GET command."""

import pytest

from app.commands.get import GetCommand
from app.storage import reset_storage, get_storage


@pytest.fixture(autouse=True)
def clean_storage():
    """Automatically reset storage before each test."""
    reset_storage()
    yield


@pytest.fixture
def get_command():
    """Fixture providing a GET command instance."""
    return GetCommand()


class TestGetCommand:
    """Test GET command implementation."""
    
    def test_get_existing_key(self, get_command):
        """GET returns value for existing key."""
        storage = get_storage()
        
        # Set up test data
        storage.set('mykey', 'myvalue')
        
        # Get it back
        result = get_command.execute(['mykey'])
        assert result == 'myvalue'
    
    def test_get_non_existent_key(self, get_command):
        """GET returns None for non-existent key."""
        result = get_command.execute(['nonexistent'])
        assert result is None
    
    def test_get_empty_value(self, get_command):
        """GET can retrieve empty string."""
        storage = get_storage()
        
        storage.set('key', '')
        result = get_command.execute(['key'])
        assert result == ''
    
    def test_get_special_characters(self, get_command):
        """GET handles special characters."""
        storage = get_storage()
        special_value = 'hello\r\n\t世界'
        
        storage.set('key', special_value)
        result = get_command.execute(['key'])
        assert result == special_value
    
    def test_get_after_overwrite(self, get_command):
        """GET returns latest value after overwrite."""
        storage = get_storage()
        
        storage.set('key', 'value1')
        storage.set('key', 'value2')
        
        result = get_command.execute(['key'])
        assert result == 'value2'
    
    def test_get_multiple_keys(self, get_command):
        """GET works with multiple keys in storage."""
        storage = get_storage()
        
        storage.set('key1', 'value1')
        storage.set('key2', 'value2')
        storage.set('key3', 'value3')
        
        assert get_command.execute(['key1']) == 'value1'
        assert get_command.execute(['key2']) == 'value2'
        assert get_command.execute(['key3']) == 'value3'
    
    def test_get_no_args(self, get_command):
        """GET without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            get_command.execute([])
    
    def test_get_too_many_args(self, get_command):
        """GET with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            get_command.execute(['key', 'extra'])
    
    def test_command_name(self, get_command):
        """Command has correct name."""
        assert get_command.name == 'GET'

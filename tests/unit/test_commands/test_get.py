"""Tests for GET command."""

import pytest

from app.commands.get import GetCommand
from app.storage import reset_storage, get_storage


class TestGetCommand:
    """Test GET command implementation."""
    
    def setup_method(self):
        """Reset storage before each test."""
        reset_storage()
    
    def test_get_existing_key(self):
        """GET returns value for existing key."""
        cmd = GetCommand()
        storage = get_storage()
        
        # Set up test data
        storage.set('mykey', 'myvalue')
        
        # Get it back
        result = cmd.execute(['mykey'])
        assert result == 'myvalue'
    
    def test_get_non_existent_key(self):
        """GET returns None for non-existent key."""
        cmd = GetCommand()
        result = cmd.execute(['nonexistent'])
        assert result is None
    
    def test_get_empty_value(self):
        """GET can retrieve empty string."""
        cmd = GetCommand()
        storage = get_storage()
        
        storage.set('key', '')
        result = cmd.execute(['key'])
        assert result == ''
    
    def test_get_special_characters(self):
        """GET handles special characters."""
        cmd = GetCommand()
        storage = get_storage()
        special_value = 'hello\r\n\t世界'
        
        storage.set('key', special_value)
        result = cmd.execute(['key'])
        assert result == special_value
    
    def test_get_after_overwrite(self):
        """GET returns latest value after overwrite."""
        cmd = GetCommand()
        storage = get_storage()
        
        storage.set('key', 'value1')
        storage.set('key', 'value2')
        
        result = cmd.execute(['key'])
        assert result == 'value2'
    
    def test_get_multiple_keys(self):
        """GET works with multiple keys in storage."""
        cmd = GetCommand()
        storage = get_storage()
        
        storage.set('key1', 'value1')
        storage.set('key2', 'value2')
        storage.set('key3', 'value3')
        
        assert cmd.execute(['key1']) == 'value1'
        assert cmd.execute(['key2']) == 'value2'
        assert cmd.execute(['key3']) == 'value3'
    
    def test_get_no_args(self):
        """GET without arguments raises error."""
        cmd = GetCommand()
        with pytest.raises(ValueError, match="wrong number of arguments"):
            cmd.execute([])
    
    def test_get_too_many_args(self):
        """GET with too many arguments raises error."""
        cmd = GetCommand()
        with pytest.raises(ValueError, match="wrong number of arguments"):
            cmd.execute(['key', 'extra'])
    
    def test_command_name(self):
        """Command has correct name."""
        cmd = GetCommand()
        assert cmd.name == 'GET'

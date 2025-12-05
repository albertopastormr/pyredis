"""Tests for SET command."""

import pytest

from app.commands.set import SetCommand
from app.storage import reset_storage, get_storage


class TestSetCommand:
    """Test SET command implementation."""
    
    def setup_method(self):
        """Reset storage before each test."""
        reset_storage()
    
    def test_set_simple_value(self):
        """SET stores a simple string value."""
        cmd = SetCommand()
        result = cmd.execute(['mykey', 'myvalue'])
        
        assert result == {'ok': 'OK'}
        
        # Verify it's actually in storage
        storage = get_storage()
        assert storage.get('mykey') == 'myvalue'
    
    def test_set_overwrites_existing(self):
        """SET overwrites existing key."""
        cmd = SetCommand()
        storage = get_storage()
        
        # Set initial value
        cmd.execute(['key', 'value1'])
        assert storage.get('key') == 'value1'
        
        # Overwrite
        result = cmd.execute(['key', 'value2'])
        assert result == {'ok': 'OK'}
        assert storage.get('key') == 'value2'
    
    def test_set_empty_value(self):
        """SET can store empty string."""
        cmd = SetCommand()
        result = cmd.execute(['key', ''])
        
        assert result == {'ok': 'OK'}
        assert get_storage().get('key') == ''
    
    def test_set_special_characters(self):
        """SET handles special characters."""
        cmd = SetCommand()
        special_value = 'hello\r\n\t世界'
        
        cmd.execute(['key', special_value])
        assert get_storage().get('key') == special_value
    
    def test_set_multiple_keys(self):
        """SET can store multiple keys."""
        cmd = SetCommand()
        storage = get_storage()
        
        cmd.execute(['key1', 'value1'])
        cmd.execute(['key2', 'value2'])
        cmd.execute(['key3', 'value3'])
        
        assert storage.get('key1') == 'value1'
        assert storage.get('key2') == 'value2'
        assert storage.get('key3') == 'value3'
        assert len(storage) == 3
    
    def test_set_no_args(self):
        """SET without arguments raises error."""
        cmd = SetCommand()
        with pytest.raises(ValueError, match="wrong number of arguments"):
            cmd.execute([])
    
    def test_set_one_arg(self):
        """SET with only key raises error."""
        cmd = SetCommand()
        with pytest.raises(ValueError, match="wrong number of arguments"):
            cmd.execute(['key'])
    
    def test_set_too_many_args(self):
        """SET with too many arguments raises error."""
        cmd = SetCommand()
        # 5 args is too many (valid is 2 or 4 with PX)
        with pytest.raises(ValueError, match="wrong number of arguments|syntax error"):
            cmd.execute(['key', 'value', 'extra', 'arg4', 'arg5'])
    
    def test_command_name(self):
        """Command has correct name."""
        cmd = SetCommand()
        assert cmd.name == 'SET'

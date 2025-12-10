"""Tests for SET command."""

import pytest

from app.commands.set import SetCommand
from app.storage import reset_storage, get_storage


@pytest.fixture(autouse=True)
def clean_storage():
    """Automatically reset storage before each test."""
    reset_storage()
    yield


@pytest.fixture
def set_command():
    """Fixture providing a SET command instance."""
    return SetCommand()


class TestSetCommand:
    """Test SET command implementation."""
    
    def test_set_simple_value(self, set_command):
        """SET stores a simple string value."""
        result = set_command.execute(['mykey', 'myvalue'])
        
        assert result == {'ok': 'OK'}
        
        # Verify it's actually in storage
        storage = get_storage()
        assert storage.get('mykey') == 'myvalue'
    
    def test_set_overwrites_existing(self, set_command):
        """SET overwrites existing key."""
        storage = get_storage()
        
        # Set initial value
        set_command.execute(['key', 'value1'])
        assert storage.get('key') == 'value1'
        
        # Overwrite
        result = set_command.execute(['key', 'value2'])
        assert result == {'ok': 'OK'}
        assert storage.get('key') == 'value2'
    
    def test_set_empty_value(self, set_command):
        """SET can store empty string."""
        result = set_command.execute(['key', ''])
        
        assert result == {'ok': 'OK'}
        assert get_storage().get('key') == ''
    
    def test_set_special_characters(self, set_command):
        """SET handles special characters."""
        special_value = 'hello\r\n\t世界'
        
        set_command.execute(['key', special_value])
        assert get_storage().get('key') == special_value
    
    def test_set_multiple_keys(self, set_command):
        """SET can store multiple keys."""
        storage = get_storage()
        
        set_command.execute(['key1', 'value1'])
        set_command.execute(['key2', 'value2'])
        set_command.execute(['key3', 'value3'])
        
        assert storage.get('key1') == 'value1'
        assert storage.get('key2') == 'value2'
        assert storage.get('key3') == 'value3'
        assert len(storage) == 3
    
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

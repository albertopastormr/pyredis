"""Integration tests for RPUSH and list commands."""

import pytest

from app.handler import execute_command
from app.resp import RESPEncoder


class TestRpushIntegration:
    """Test RPUSH integration with storage."""
    
    def test_rpush_creates_new_list(self):
        """RPUSH creates a new list with first element."""
        result = execute_command(['RPUSH', 'mylist', 'foo'])
        
        assert result == 1
    
    def test_rpush_appends_to_list(self):
        """RPUSH appends to existing list."""
        execute_command(['RPUSH', 'mylist', 'first'])
        result = execute_command(['RPUSH', 'mylist', 'second'])
        
        assert result == 2
    
    def test_rpush_multiple_values(self):
        """RPUSH with multiple values in one command."""
        result = execute_command(['RPUSH', 'mylist', 'a', 'b', 'c'])
        
        assert result == 3
    
    def test_rpush_returns_integer_in_resp(self):
        """RPUSH returns integer in RESP format."""
        result = execute_command(['RPUSH', 'list', 'value'])
        response = RESPEncoder.encode(result)
        
        # Integer 1 encoded as :1\r\n
        assert response == b":1\r\n"
    
    def test_rpush_increments_length(self):
        """Multiple RPUSH calls increment length."""
        assert execute_command(['RPUSH', 'mylist', 'a']) == 1
        assert execute_command(['RPUSH', 'mylist', 'b']) == 2
        assert execute_command(['RPUSH', 'mylist', 'c']) == 3
        assert execute_command(['RPUSH', 'mylist', 'd']) == 4
    
    def test_rpush_with_empty_string(self):
        """RPUSH handles empty string values."""
        result = execute_command(['RPUSH', 'mylist', ''])
        
        assert result == 1
    
    def test_rpush_different_lists(self):
        """RPUSH on different lists are independent."""
        execute_command(['RPUSH', 'list1', 'a', 'b'])
        execute_command(['RPUSH', 'list2', 'x'])
        
        result1 = execute_command(['RPUSH', 'list1', 'c'])
        result2 = execute_command(['RPUSH', 'list2', 'y'])
        
        assert result1 == 3  # list1 has 3 elements
        assert result2 == 2  # list2 has 2 elements


class TestListTypeConflicts:
    """Test type conflicts between lists and other types."""
    
    def test_rpush_on_string_key_raises_error(self):
        """RPUSH on a string key raises WRONGTYPE."""
        execute_command(['SET', 'mykey', 'string value'])
        
        with pytest.raises(ValueError, match="WRONGTYPE"):
            execute_command(['RPUSH', 'mykey', 'list value'])
    
    def test_get_on_list_key_raises_error(self):
        """GET on a list key raises WRONGTYPE."""
        execute_command(['RPUSH', 'mylist', 'value'])
        
        with pytest.raises(ValueError, match="WRONGTYPE"):
            execute_command(['GET', 'mylist'])
    
    def test_set_overwrites_list(self):
        """SET overwrites a list with a string."""
        execute_command(['RPUSH', 'mykey', 'a', 'b', 'c'])
        execute_command(['SET', 'mykey', 'string'])
        
        # Now it's a string
        result = execute_command(['GET', 'mykey'])
        assert result == 'string'
    
    def test_rpush_after_set_creates_new_list(self):
        """RPUSH after SET creates new list."""
        execute_command(['SET', 'mykey', 'string'])
        execute_command(['SET', 'otherkey', 'value'])  # Different key
        execute_command(['RPUSH', 'newlist', 'item'])
        
        result = execute_command(['RPUSH', 'newlist', 'item2'])
        assert result == 2


class TestRpushErrors:
    """Test RPUSH error cases."""
    
    def test_rpush_no_args(self):
        """RPUSH without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['RPUSH'])
    
    def test_rpush_one_arg(self):
        """RPUSH with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['RPUSH', 'key'])
    
    def test_rpush_case_insensitive(self):
        """RPUSH is case-insensitive."""
        result1 = execute_command(['rpush', 'list', 'a'])
        result2 = execute_command(['RPUSH', 'list', 'b'])
        result3 = execute_command(['RpUsH', 'list', 'c'])
        
        assert result1 == 1
        assert result2 == 2
        assert result3 == 3

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


class TestLrangeIntegration:
    """Test LRANGE integration with storage."""
    
    def test_lrange_basic(self):
        """LRANGE returns elements in range."""
        execute_command(['RPUSH', 'mylist', 'a', 'b', 'c', 'd', 'e'])
        
        result = execute_command(['LRANGE', 'mylist', '0', '2'])
        assert result == ['a', 'b', 'c']
    
    def test_lrange_stop_greater_than_length(self):
        """LRANGE treats stop > length as length."""
        execute_command(['RPUSH', 'mylist', 'a', 'b', 'c'])
        
        result = execute_command(['LRANGE', 'mylist', '0', '10'])
        assert result == ['a', 'b', 'c']
    
    def test_lrange_start_greater_than_stop(self):
        """LRANGE returns empty when start > stop."""
        execute_command(['RPUSH', 'mylist', 'a', 'b', 'c', 'd'])
        
        result = execute_command(['LRANGE', 'mylist', '3', '1'])
        assert result == []
    
    def test_lrange_start_greater_than_length(self):
        """LRANGE returns empty when start > length."""
        execute_command(['RPUSH', 'mylist', 'a', 'b', 'c'])
        
        result = execute_command(['LRANGE', 'mylist', '10', '20'])
        assert result == []
    
    def test_lrange_nonexistent_key(self):
        """LRANGE on non-existent key returns empty list."""
        result = execute_command(['LRANGE', 'nonexistent', '0', '5'])
        assert result == []
    
    def test_lrange_full_list(self):
        """LRANGE can return full list."""
        execute_command(['RPUSH', 'mylist', 'a', 'b', 'c', 'd'])
        
        result = execute_command(['LRANGE', 'mylist', '0', '10'])
        assert result == ['a', 'b', 'c', 'd']
    
    def test_lrange_middle_range(self):
        """LRANGE can return middle portion."""
        execute_command(['RPUSH', 'mylist', 'a', 'b', 'c', 'd', 'e'])
        
        result = execute_command(['LRANGE', 'mylist', '1', '3'])
        assert result == ['b', 'c', 'd']
    
    def test_lrange_single_element(self):
        """LRANGE can return single element."""
        execute_command(['RPUSH', 'mylist', 'a', 'b', 'c'])
        
        result = execute_command(['LRANGE', 'mylist', '1', '1'])
        assert result == ['b']
    
    def test_lrange_returns_array_in_resp(self):
        """LRANGE returns array in RESP format."""
        execute_command(['RPUSH', 'list', 'foo', 'bar'])
        result = execute_command(['LRANGE', 'list', '0', '1'])
        response = RESPEncoder.encode(result)
        
        # Array of 2 bulk strings
        assert response == b"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"
    
    def test_lrange_negative_indices(self):
        """LRANGE supports negative indices."""
        execute_command(['RPUSH', 'mylist', 'a', 'b', 'c', 'd', 'e'])
        
        # Get last element
        result = execute_command(['LRANGE', 'mylist', '-1', '-1'])
        assert result == ['e']
        
        # Get last 3 elements
        result = execute_command(['LRANGE', 'mylist', '-3', '-1'])
        assert result == ['c', 'd', 'e']
        
        # Get full list with negative
        result = execute_command(['LRANGE', 'mylist', '0', '-1'])
        assert result == ['a', 'b', 'c', 'd', 'e']
    
    def test_lrange_mixed_indices(self):
        """LRANGE supports mixed positive and negative indices."""
        execute_command(['RPUSH', 'mylist', 'a', 'b', 'c', 'd', 'e'])
        
        # Positive start, negative stop
        result = execute_command(['LRANGE', 'mylist', '1', '-2'])
        assert result == ['b', 'c', 'd']
        
        # Negative start, positive stop
        result = execute_command(['LRANGE', 'mylist', '-4', '3'])
        assert result == ['b', 'c', 'd']
    
    def test_lrange_negative_out_of_bounds(self):
        """LRANGE handles out of bounds negative indices."""
        execute_command(['RPUSH', 'mylist', 'a', 'b', 'c'])
        
        # Start too negative
        result = execute_command(['LRANGE', 'mylist', '-10', '-1'])
        assert result == []
        
        # Reversed (stop before start after conversion)
        result = execute_command(['LRANGE', 'mylist', '-1', '-3'])
        assert result == []


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
    
    def test_lrange_on_string_key_raises_error(self):
        """LRANGE on a string key raises WRONGTYPE."""
        execute_command(['SET', 'mykey', 'string value'])
        
        with pytest.raises(ValueError, match="WRONGTYPE"):
            execute_command(['LRANGE', 'mykey', '0', '5'])
    
    def test_lrange_no_args(self):
        """LRANGE without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['LRANGE'])
    
    def test_lrange_one_arg(self):
        """LRANGE with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['LRANGE', 'key'])
    
    def test_lrange_two_args(self):
        """LRANGE with only key and start raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(['LRANGE', 'key', '0'])
    
    def test_lrange_invalid_start(self):
        """LRANGE with non-integer start raises error."""
        execute_command(['RPUSH', 'mylist', 'a'])
        
        with pytest.raises(ValueError, match="not an integer"):
            execute_command(['LRANGE', 'mylist', 'abc', '5'])
    
    def test_lrange_invalid_stop(self):
        """LRANGE with non-integer stop raises error."""
        execute_command(['RPUSH', 'mylist', 'a'])
        
        with pytest.raises(ValueError, match="not an integer"):
            execute_command(['LRANGE', 'mylist', '0', 'xyz'])

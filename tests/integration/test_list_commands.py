"""Integration tests for RPUSH and list commands."""

import pytest

from app.resp import RESPEncoder
from tests.helpers import execute_command


class TestRpushIntegration:
    """Test RPUSH integration with storage."""

    def test_rpush_creates_new_list(self):
        """RPUSH creates a new list with first element."""
        result = execute_command(["RPUSH", "mylist", "foo"])

        assert result == 1

    def test_rpush_appends_to_list(self):
        """RPUSH appends to existing list."""
        execute_command(["RPUSH", "mylist", "first"])
        result = execute_command(["RPUSH", "mylist", "second"])

        assert result == 2

    def test_rpush_multiple_values(self):
        """RPUSH with multiple values in one command."""
        result = execute_command(["RPUSH", "mylist", "a", "b", "c"])

        assert result == 3

    def test_rpush_returns_integer_in_resp(self):
        """RPUSH returns integer in RESP format."""
        result = execute_command(["RPUSH", "list", "value"])
        response = RESPEncoder.encode(result)

        # Integer 1 encoded as :1\r\n
        assert response == b":1\r\n"

    def test_rpush_increments_length(self):
        """Multiple RPUSH calls increment length."""
        assert execute_command(["RPUSH", "mylist", "a"]) == 1
        assert execute_command(["RPUSH", "mylist", "b"]) == 2
        assert execute_command(["RPUSH", "mylist", "c"]) == 3
        assert execute_command(["RPUSH", "mylist", "d"]) == 4

    def test_rpush_with_empty_string(self):
        """RPUSH handles empty string values."""
        result = execute_command(["RPUSH", "mylist", ""])

        assert result == 1

    def test_rpush_different_lists(self):
        """RPUSH on different lists are independent."""
        execute_command(["RPUSH", "list1", "a", "b"])
        execute_command(["RPUSH", "list2", "x"])

        result1 = execute_command(["RPUSH", "list1", "c"])
        result2 = execute_command(["RPUSH", "list2", "y"])

        assert result1 == 3  # list1 has 3 elements
        assert result2 == 2  # list2 has 2 elements


class TestLpushIntegration:
    """Test LPUSH integration with storage."""

    def test_lpush_creates_new_list(self):
        """LPUSH creates a new list with first element."""
        result = execute_command(["LPUSH", "mylist", "foo"])

        assert result == 1

    def test_lpush_prepends_to_list(self):
        """LPUSH prepends to existing list."""
        execute_command(["LPUSH", "mylist", "second"])
        result = execute_command(["LPUSH", "mylist", "first"])

        assert result == 2

        # Verify order
        items = execute_command(["LRANGE", "mylist", "0", "-1"])
        assert items == ["first", "second"]

    def test_lpush_multiple_values(self):
        """LPUSH with multiple values in one command."""
        result = execute_command(["LPUSH", "mylist", "a", "b", "c"])

        assert result == 3

        # Multiple values are prepended in order: c, b, a
        items = execute_command(["LRANGE", "mylist", "0", "-1"])
        assert items == ["c", "b", "a"]

    def test_lpush_returns_integer_in_resp(self):
        """LPUSH returns integer in RESP format."""
        result = execute_command(["LPUSH", "list", "value"])
        response = RESPEncoder.encode(result)

        # Integer 1 encoded as :1\r\n
        assert response == b":1\r\n"

    def test_lpush_increments_length(self):
        """Multiple LPUSH calls increment length."""
        assert execute_command(["LPUSH", "mylist", "a"]) == 1
        assert execute_command(["LPUSH", "mylist", "b"]) == 2
        assert execute_command(["LPUSH", "mylist", "c"]) == 3
        assert execute_command(["LPUSH", "mylist", "d"]) == 4

    def test_lpush_with_empty_string(self):
        """LPUSH handles empty string values."""
        result = execute_command(["LPUSH", "mylist", ""])

        assert result == 1

    def test_lpush_and_rpush_combination(self):
        """LPUSH and RPUSH work together correctly."""
        execute_command(["RPUSH", "mylist", "d", "e"])  # [d, e]
        execute_command(["LPUSH", "mylist", "b", "c"])  # [c, b, d, e]
        execute_command(["LPUSH", "mylist", "a"])  # [a, c, b, d, e]
        execute_command(["RPUSH", "mylist", "f"])  # [a, c, b, d, e, f]

        items = execute_command(["LRANGE", "mylist", "0", "-1"])
        assert items == ["a", "c", "b", "d", "e", "f"]

    def test_lpush_different_lists(self):
        """LPUSH on different lists are independent."""
        execute_command(["LPUSH", "list1", "a", "b"])
        execute_command(["LPUSH", "list2", "x"])

        result1 = execute_command(["LPUSH", "list1", "c"])
        result2 = execute_command(["LPUSH", "list2", "y"])

        assert result1 == 3  # list1 has 3 elements
        assert result2 == 2  # list2 has 2 elements


class TestLrangeIntegration:
    """Test LRANGE integration with storage."""

    def test_lrange_basic(self):
        """LRANGE returns elements in range."""
        execute_command(["RPUSH", "mylist", "a", "b", "c", "d", "e"])

        result = execute_command(["LRANGE", "mylist", "0", "2"])
        assert result == ["a", "b", "c"]

    def test_lrange_stop_greater_than_length(self):
        """LRANGE treats stop > length as length."""
        execute_command(["RPUSH", "mylist", "a", "b", "c"])

        result = execute_command(["LRANGE", "mylist", "0", "10"])
        assert result == ["a", "b", "c"]

    def test_lrange_start_greater_than_stop(self):
        """LRANGE returns empty when start > stop."""
        execute_command(["RPUSH", "mylist", "a", "b", "c", "d"])

        result = execute_command(["LRANGE", "mylist", "3", "1"])
        assert result == []

    def test_lrange_start_greater_than_length(self):
        """LRANGE returns empty when start > length."""
        execute_command(["RPUSH", "mylist", "a", "b", "c"])

        result = execute_command(["LRANGE", "mylist", "10", "20"])
        assert result == []

    def test_lrange_nonexistent_key(self):
        """LRANGE on non-existent key returns empty list."""
        result = execute_command(["LRANGE", "nonexistent", "0", "5"])
        assert result == []

    def test_lrange_full_list(self):
        """LRANGE can return full list."""
        execute_command(["RPUSH", "mylist", "a", "b", "c", "d"])

        result = execute_command(["LRANGE", "mylist", "0", "10"])
        assert result == ["a", "b", "c", "d"]

    def test_lrange_middle_range(self):
        """LRANGE can return middle portion."""
        execute_command(["RPUSH", "mylist", "a", "b", "c", "d", "e"])

        result = execute_command(["LRANGE", "mylist", "1", "3"])
        assert result == ["b", "c", "d"]

    def test_lrange_single_element(self):
        """LRANGE can return single element."""
        execute_command(["RPUSH", "mylist", "a", "b", "c"])

        result = execute_command(["LRANGE", "mylist", "1", "1"])
        assert result == ["b"]

    def test_lrange_returns_array_in_resp(self):
        """LRANGE returns array in RESP format."""
        execute_command(["RPUSH", "list", "foo", "bar"])
        result = execute_command(["LRANGE", "list", "0", "1"])
        response = RESPEncoder.encode(result)

        # Array of 2 bulk strings
        assert response == b"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n"

    def test_lrange_negative_indices(self):
        """LRANGE supports negative indices."""
        execute_command(["RPUSH", "mylist", "a", "b", "c", "d", "e"])

        # Get last element
        result = execute_command(["LRANGE", "mylist", "-1", "-1"])
        assert result == ["e"]

        # Get last 3 elements
        result = execute_command(["LRANGE", "mylist", "-3", "-1"])
        assert result == ["c", "d", "e"]

        # Get full list with negative
        result = execute_command(["LRANGE", "mylist", "0", "-1"])
        assert result == ["a", "b", "c", "d", "e"]

    def test_lrange_mixed_indices(self):
        """LRANGE supports mixed positive and negative indices."""
        execute_command(["RPUSH", "mylist", "a", "b", "c", "d", "e"])

        # Positive start, negative stop
        result = execute_command(["LRANGE", "mylist", "1", "-2"])
        assert result == ["b", "c", "d"]

        # Negative start, positive stop
        result = execute_command(["LRANGE", "mylist", "-4", "3"])
        assert result == ["b", "c", "d"]

    def test_lrange_negative_out_of_bounds(self):
        """LRANGE handles out of bounds negative indices."""
        execute_command(["RPUSH", "mylist", "a", "b", "c"])

        # Start too negative - should clamp to 0 and return from start
        result = execute_command(["LRANGE", "mylist", "-10", "-1"])
        assert result == ["a", "b", "c"]

        # Stop too negative - should clamp to 0
        result = execute_command(["LRANGE", "mylist", "0", "-10"])
        assert result == ["a"]

        # Reversed (stop before start after conversion)
        result = execute_command(["LRANGE", "mylist", "-1", "-3"])
        assert result == []


class TestListTypeConflicts:
    """Test type conflicts between lists and other types."""

    def test_rpush_on_string_key_raises_error(self):
        """RPUSH on a string key raises WRONGTYPE."""
        execute_command(["SET", "mykey", "string value"])

        with pytest.raises(ValueError, match="WRONGTYPE"):
            execute_command(["RPUSH", "mykey", "list value"])

    def test_get_on_list_key_raises_error(self):
        """GET on a list key raises WRONGTYPE."""
        execute_command(["RPUSH", "mylist", "value"])

        with pytest.raises(ValueError, match="WRONGTYPE"):
            execute_command(["GET", "mylist"])

    def test_set_overwrites_list(self):
        """SET overwrites a list with a string."""
        execute_command(["RPUSH", "mykey", "a", "b", "c"])
        execute_command(["SET", "mykey", "string"])

        # Now it's a string
        result = execute_command(["GET", "mykey"])
        assert result == "string"

    def test_rpush_after_set_creates_new_list(self):
        """RPUSH after SET creates new list."""
        execute_command(["SET", "mykey", "string"])
        execute_command(["SET", "otherkey", "value"])  # Different key
        execute_command(["RPUSH", "newlist", "item"])

        result = execute_command(["RPUSH", "newlist", "item2"])
        assert result == 2


class TestRpushErrors:
    """Test RPUSH error cases."""

    def test_rpush_no_args(self):
        """RPUSH without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["RPUSH"])

    def test_rpush_one_arg(self):
        """RPUSH with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["RPUSH", "key"])

    def test_rpush_case_insensitive(self):
        """RPUSH is case-insensitive."""
        result1 = execute_command(["rpush", "list", "a"])
        result2 = execute_command(["RPUSH", "list", "b"])
        result3 = execute_command(["RpUsH", "list", "c"])

        assert result1 == 1
        assert result2 == 2
        assert result3 == 3

    def test_lpush_on_string_key_raises_error(self):
        """LPUSH on a string key raises WRONGTYPE."""
        execute_command(["SET", "mykey", "string value"])

        with pytest.raises(ValueError, match="WRONGTYPE"):
            execute_command(["LPUSH", "mykey", "list value"])

    def test_lpush_no_args(self):
        """LPUSH without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["LPUSH"])

    def test_lpush_one_arg(self):
        """LPUSH with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["LPUSH", "key"])

    def test_lpush_case_insensitive(self):
        """LPUSH is case-insensitive."""
        result1 = execute_command(["lpush", "list", "a"])
        result2 = execute_command(["LPUSH", "list", "b"])
        result3 = execute_command(["LpUsH", "list", "c"])

        assert result1 == 1
        assert result2 == 2
        assert result3 == 3

    def test_lrange_on_string_key_raises_error(self):
        """LRANGE on a string key raises WRONGTYPE."""
        execute_command(["SET", "mykey", "string value"])

        with pytest.raises(ValueError, match="WRONGTYPE"):
            execute_command(["LRANGE", "mykey", "0", "5"])

    def test_lrange_no_args(self):
        """LRANGE without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["LRANGE"])

    def test_lrange_one_arg(self):
        """LRANGE with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["LRANGE", "key"])

    def test_lrange_two_args(self):
        """LRANGE with only key and start raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["LRANGE", "key", "0"])

    def test_lrange_invalid_start(self):
        """LRANGE with non-integer start raises error."""
        execute_command(["RPUSH", "mylist", "a"])

        with pytest.raises(ValueError, match="not an integer"):
            execute_command(["LRANGE", "mylist", "abc", "5"])

    def test_lrange_invalid_stop(self):
        """LRANGE with non-integer stop raises error."""
        execute_command(["RPUSH", "mylist", "a"])

        with pytest.raises(ValueError, match="not an integer"):
            execute_command(["LRANGE", "mylist", "0", "xyz"])


class TestLlenIntegration:
    """Test LLEN integration with storage."""

    def test_llen_nonexistent_key(self):
        """LLEN returns 0 for non-existent key."""
        result = execute_command(["LLEN", "nonexistent"])
        assert result == 0

    def test_llen_after_rpush(self):
        """LLEN returns correct length after RPUSH."""
        execute_command(["RPUSH", "mylist", "a", "b", "c"])
        result = execute_command(["LLEN", "mylist"])
        assert result == 3

    def test_llen_after_lpush(self):
        """LLEN returns correct length after LPUSH."""
        execute_command(["LPUSH", "mylist", "x", "y", "z"])
        result = execute_command(["LLEN", "mylist"])
        assert result == 3

    def test_llen_after_mixed_operations(self):
        """LLEN returns correct length after mixed operations."""
        execute_command(["RPUSH", "mylist", "a", "b"])
        execute_command(["LPUSH", "mylist", "x"])
        execute_command(["RPUSH", "mylist", "c"])
        result = execute_command(["LLEN", "mylist"])
        assert result == 4

    def test_llen_single_element(self):
        """LLEN returns 1 for single element list."""
        execute_command(["RPUSH", "mylist", "only"])
        result = execute_command(["LLEN", "mylist"])
        assert result == 1

    def test_llen_returns_integer_in_resp(self):
        """LLEN returns integer in RESP format."""
        execute_command(["RPUSH", "list", "a", "b", "c"])
        result = execute_command(["LLEN", "list"])
        response = RESPEncoder.encode(result)
        assert response == b":3\r\n"

    def test_llen_different_lists(self):
        """LLEN on different lists are independent."""
        execute_command(["RPUSH", "list1", "a", "b", "c"])
        execute_command(["RPUSH", "list2", "x"])
        result1 = execute_command(["LLEN", "list1"])
        result2 = execute_command(["LLEN", "list2"])
        assert result1 == 3
        assert result2 == 1

    def test_llen_on_string_key_raises_error(self):
        """LLEN on a string key raises WRONGTYPE."""
        execute_command(["SET", "mykey", "string value"])
        with pytest.raises(ValueError, match="WRONGTYPE"):
            execute_command(["LLEN", "mykey"])

    def test_llen_no_args(self):
        """LLEN without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["LLEN"])

    def test_llen_too_many_args(self):
        """LLEN with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["LLEN", "key", "extra"])

    def test_llen_case_insensitive(self):
        """LLEN is case-insensitive."""
        execute_command(["RPUSH", "list", "a", "b"])
        result1 = execute_command(["llen", "list"])
        result2 = execute_command(["LLEN", "list"])
        result3 = execute_command(["LlEn", "list"])
        assert result1 == 2
        assert result2 == 2
        assert result3 == 2


class TestLpopIntegration:
    """Test LPOP integration with storage."""

    def test_lpop_single_element(self):
        """LPOP removes and returns single element."""
        execute_command(["RPUSH", "mylist", "a", "b", "c"])
        result = execute_command(["LPOP", "mylist"])

        assert result == "a"
        remaining = execute_command(["LRANGE", "mylist", "0", "-1"])
        assert remaining == ["b", "c"]

    def test_lpop_with_count(self):
        """LPOP with count removes and returns multiple elements."""
        execute_command(["RPUSH", "mylist", "a", "b", "c", "d", "e"])
        result = execute_command(["LPOP", "mylist", "3"])

        assert result == ["a", "b", "c"]
        remaining = execute_command(["LRANGE", "mylist", "0", "-1"])
        assert remaining == ["d", "e"]

    def test_lpop_count_greater_than_length(self):
        """LPOP with count > length returns all elements."""
        execute_command(["RPUSH", "mylist", "x", "y"])
        result = execute_command(["LPOP", "mylist", "10"])

        assert result == ["x", "y"]
        # List should be deleted
        length = execute_command(["LLEN", "mylist"])
        assert length == 0

    def test_lpop_nonexistent_key(self):
        """LPOP on non-existent key returns None."""
        result = execute_command(["LPOP", "doesnotexist", "1"])
        assert result is None

    def test_lpop_until_empty(self):
        """LPOP until list is empty."""
        execute_command(["RPUSH", "mylist", "a", "b"])

        result1 = execute_command(["LPOP", "mylist"])
        assert result1 == "a"

        result2 = execute_command(["LPOP", "mylist"])
        assert result2 == "b"

        # List should be empty and deleted
        result3 = execute_command(["LPOP", "mylist"])
        assert result3 is None

    def test_lpop_returns_bulk_string_in_resp(self):
        """LPOP (single) returns bulk string in RESP format."""
        execute_command(["RPUSH", "list", "foo"])
        result = execute_command(["LPOP", "list"])
        response = RESPEncoder.encode(result)

        # Bulk string "foo"
        assert response == b"$3\r\nfoo\r\n"

    def test_lpop_returns_array_in_resp(self):
        """LPOP with count returns array in RESP format."""
        execute_command(["RPUSH", "list", "a", "b", "c"])
        result = execute_command(["LPOP", "list", "2"])
        response = RESPEncoder.encode(result)

        # Array of 2 bulk strings
        assert response == b"*2\r\n$1\r\na\r\n$1\r\nb\r\n"

    def test_lpop_returns_null_in_resp(self):
        """LPOP on non-existent returns null in RESP format."""
        result = execute_command(["LPOP", "nonexistent"])
        response = RESPEncoder.encode(result)

        # Null bulk string
        assert response == b"$-1\r\n"

    def test_lpop_on_string_key_raises_error(self):
        """LPOP on a string key raises WRONGTYPE."""
        execute_command(["SET", "mykey", "string value"])

        with pytest.raises(ValueError, match="WRONGTYPE"):
            execute_command(["LPOP", "mykey"])

    def test_lpop_no_args(self):
        """LPOP without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["LPOP"])

    def test_lpop_too_many_args(self):
        """LPOP with too many arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["LPOP", "key", "1", "extra"])

    def test_lpop_invalid_count(self):
        """LPOP with non-integer count raises error."""
        execute_command(["RPUSH", "mylist", "a"])

        with pytest.raises(ValueError, match="not an integer"):
            execute_command(["LPOP", "mylist", "abc"])

    def test_lpop_negative_count(self):
        """LPOP with negative count raises error."""
        execute_command(["RPUSH", "mylist", "a"])

        with pytest.raises(ValueError, match="out of range"):
            execute_command(["LPOP", "mylist", "-1"])

    def test_lpop_case_insensitive(self):
        """LPOP is case-insensitive."""
        execute_command(["RPUSH", "list", "a", "b"])

        result1 = execute_command(["lpop", "list"])
        result2 = execute_command(["LPOP", "list"])

        assert result1 == "a"
        assert result2 == "b"


class TestBlpopIntegration:
    """Test BLPOP integration with storage."""

    def test_blpop_immediate_return_with_element(self):
        """BLPOP returns immediately if element available."""
        execute_command(["RPUSH", "mylist", "a", "b"])
        result = execute_command(["BLPOP", "mylist", "5"])

        assert result == ["mylist", "a"]
        # Verify element was removed
        remaining = execute_command(["LRANGE", "mylist", "0", "-1"])
        assert remaining == ["b"]

    def test_blpop_timeout_on_empty_list(self):
        """BLPOP returns None after timeout on empty list."""
        import time

        start = time.monotonic()
        result = execute_command(["BLPOP", "empty", "0.5"])
        elapsed = time.monotonic() - start

        assert result == {"null_array": True}
        assert 0.4 < elapsed < 1.0  # Should timeout around 0.5s

    def test_blpop_timeout_on_nonexistent_key(self):
        """BLPOP returns None after timeout on non-existent key."""
        import time

        start = time.monotonic()
        result = execute_command(["BLPOP", "nonexistent", "0.5"])
        elapsed = time.monotonic() - start

        assert result == {"null_array": True}
        assert 0.4 < elapsed < 1.0

    def test_blpop_returns_array_in_resp(self):
        """BLPOP returns array [key, value] in RESP format."""
        execute_command(["RPUSH", "list", "foo"])
        result = execute_command(["BLPOP", "list", "1"])
        response = RESPEncoder.encode(result)

        # Array with 2 bulk strings
        assert response == b"*2\r\n$4\r\nlist\r\n$3\r\nfoo\r\n"

    def test_blpop_returns_null_in_resp(self):
        """BLPOP timeout returns RESP null array (*-1\r\n)."""
        result = execute_command(["BLPOP", "nonexistent", "0.1"])

        # Should return null array marker
        assert result == {"null_array": True}

        # Verify RESP encoding
        from app.resp import RESPEncoder

        response = RESPEncoder.encode(result)
        assert response == b"*-1\r\n"  # Null array for BLPOP timeout

    def test_blpop_zero_timeout_mechanism(self):
        """BLPOP with timeout=0 waits but has safety limit."""
        # Note: We can't truly test indefinite blocking without async operations
        # This test just verifies that timeout=0 is accepted
        execute_command(["RPUSH", "list", "item"])
        result = execute_command(["BLPOP", "list", "0"])

        # Should return immediately since list has an element
        assert result == ["list", "item"]

    def test_blpop_on_string_key_immediate_return(self):
        """BLPOP on string key returns immediately (finds no list)."""
        execute_command(["SET", "mykey", "string value"])
        import time

        start = time.monotonic()
        result = execute_command(["BLPOP", "mykey", "0.5"])
        elapsed = time.monotonic() - start

        # Should timeout since it's not a list
        assert result == {"null_array": True}
        assert 0.4 < elapsed < 1.0

    def test_blpop_no_args(self):
        """BLPOP without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["BLPOP"])

    def test_blpop_one_arg(self):
        """BLPOP with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["BLPOP", "key"])

    def test_blpop_invalid_timeout(self):
        """BLPOP with non-numeric timeout raises error."""
        with pytest.raises(ValueError, match="not a float"):
            execute_command(["BLPOP", "key", "abc"])

    def test_blpop_negative_timeout(self):
        """BLPOP with negative timeout raises error."""
        with pytest.raises(ValueError, match="negative"):
            execute_command(["BLPOP", "key", "-1"])

    def test_blpop_case_insensitive(self):
        """BLPOP is case-insensitive."""
        execute_command(["RPUSH", "list", "a"])
        result = execute_command(["blpop", "list", "1"])

        assert result == ["list", "a"]

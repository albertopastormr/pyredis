"""Integration tests for XRANGE command."""

import pytest

from tests.helpers import execute_command


class TestXrangeIntegration:
    """Test XRANGE command with real storage."""

    def test_xrange_basic(self):
        """XRANGE retrieves entries in range."""
        execute_command(["XADD", "stream", "1-0", "a", "1"])
        execute_command(["XADD", "stream", "2-0", "b", "2"])
        execute_command(["XADD", "stream", "3-0", "c", "3"])

        result = execute_command(["XRANGE", "stream", "1-0", "2-0"])
        
        assert len(result) == 2
        assert result[0] == ["1-0", ["a", "1"]]
        assert result[1] == ["2-0", ["b", "2"]]

    def test_xrange_inclusive(self):
        """XRANGE is inclusive on both ends."""
        execute_command(["XADD", "stream", "1-0", "a", "1"])
        execute_command(["XADD", "stream", "2-0", "b", "2"])
        execute_command(["XADD", "stream", "3-0", "c", "3"])

        result = execute_command(["XRANGE", "stream", "2-0", "3-0"])
        
        assert len(result) == 2
        assert result[0][0] == "2-0"
        assert result[1][0] == "3-0"

    def test_xrange_no_sequence_number_start(self):
        """XRANGE without sequence in start defaults to 0."""
        execute_command(["XADD", "stream", "100-0", "a", "1"])
        execute_command(["XADD", "stream", "100-5", "b", "2"])
        execute_command(["XADD", "stream", "100-10", "c", "3"])

        result = execute_command(["XRANGE", "stream", "100", "100-10"])
        
        # Should include 100-0 (start defaults to 100-0)
        assert len(result) == 3
        assert result[0][0] == "100-0"

    def test_xrange_no_sequence_number_end(self):
        """XRANGE without sequence in end defaults to max."""
        execute_command(["XADD", "stream", "100-0", "a", "1"])
        execute_command(["XADD", "stream", "100-5", "b", "2"])
        execute_command(["XADD", "stream", "100-10", "c", "3"])

        result = execute_command(["XRANGE", "stream", "100-5", "100"])
        
        # Should include 100-5 and 100-10 (end defaults to 100-max)
        assert len(result) == 2
        assert result[0][0] == "100-5"
        assert result[1][0] == "100-10"

    def test_xrange_no_sequence_number_both(self):
        """XRANGE without sequence in both start and end."""
        execute_command(["XADD", "stream", "100-0", "a", "1"])
        execute_command(["XADD", "stream", "100-5", "b", "2"])
        execute_command(["XADD", "stream", "200-0", "c", "3"])

        result = execute_command(["XRANGE", "stream", "100", "100"])
        
        # Should get all entries with timestamp 100
        assert len(result) == 2
        assert result[0][0] == "100-0"
        assert result[1][0] == "100-5"

    def test_xrange_empty_stream(self):
        """XRANGE on non-existent stream returns empty array."""
        result = execute_command(["XRANGE", "nonexistent", "1-0", "2-0"])
        assert result == []

    def test_xrange_no_entries_in_range(self):
        """XRANGE with no entries in range returns empty."""
        execute_command(["XADD", "stream", "1-0", "a", "1"])
        execute_command(["XADD", "stream", "10-0", "b", "2"])

        result = execute_command(["XRANGE", "stream", "2-0", "9-0"])
        assert result == []

    def test_xrange_single_entry(self):
        """XRANGE can return single entry."""
        execute_command(["XADD", "stream", "5-0", "foo", "bar"])

        result = execute_command(["XRANGE", "stream", "5-0", "5-0"])
        
        assert len(result) == 1
        assert result[0] == ["5-0", ["foo", "bar"]]

    def test_xrange_multiple_fields(self):
        """XRANGE preserves multiple field-value pairs."""
        execute_command(["XADD", "stream", "1-0", "a", "1", "b", "2", "c", "3"])

        result = execute_command(["XRANGE", "stream", "1-0", "1-0"])
        
        assert len(result) == 1
        assert result[0][0] == "1-0"
        assert result[0][1] == ["a", "1", "b", "2", "c", "3"]

    def test_xrange_all_entries(self):
        """XRANGE can retrieve all entries with wide range."""
        execute_command(["XADD", "stream", "1-0", "a", "1"])
        execute_command(["XADD", "stream", "2-0", "b", "2"])
        execute_command(["XADD", "stream", "3-0", "c", "3"])

        result = execute_command(["XRANGE", "stream", "0-0", "999999999-0"])
        
        assert len(result) == 3

    def test_xrange_reverse_range(self):
        """XRANGE with start > end returns empty."""
        execute_command(["XADD", "stream", "1-0", "a", "1"])
        execute_command(["XADD", "stream", "2-0", "b", "2"])

        result = execute_command(["XRANGE", "stream", "2-0", "1-0"])
        assert result == []

    def test_xrange_preserves_order(self):
        """XRANGE returns entries in chronological order."""
        execute_command(["XADD", "stream", "1-0", "a", "1"])
        execute_command(["XADD", "stream", "2-0", "b", "2"])
        execute_command(["XADD", "stream", "3-0", "c", "3"])

        result = execute_command(["XRANGE", "stream", "1-0", "3-0"])
        
        assert len(result) == 3
        assert result[0][0] == "1-0"
        assert result[1][0] == "2-0"
        assert result[2][0] == "3-0"


class TestXrangeErrors:
    """Test XRANGE error handling."""

    def test_xrange_no_args(self):
        """XRANGE without args raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["XRANGE"])

    def test_xrange_one_arg(self):
        """XRANGE with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["XRANGE", "key"])

    def test_xrange_two_args(self):
        """XRANGE with only key and start raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["XRANGE", "key", "1-0"])

    def test_xrange_too_many_args(self):
        """XRANGE with too many args raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["XRANGE", "key", "1-0", "2-0", "extra"])

    def test_xrange_on_string_key_fails(self):
        """XRANGE on string key raises WRONGTYPE error."""
        from app.exceptions import WrongTypeError

        execute_command(["SET", "mykey", "value"])

        with pytest.raises(WrongTypeError):
            execute_command(["XRANGE", "mykey", "1-0", "2-0"])

    def test_xrange_on_list_key_fails(self):
        """XRANGE on list key raises WRONGTYPE error."""
        from app.exceptions import WrongTypeError

        execute_command(["RPUSH", "mylist", "item"])

        with pytest.raises(WrongTypeError):
            execute_command(["XRANGE", "mylist", "1-0", "2-0"])

    def test_xrange_case_insensitive(self):
        """XRANGE command is case-insensitive."""
        execute_command(["XADD", "stream", "1-0", "a", "1"])

        result1 = execute_command(["XRANGE", "stream", "1-0", "1-0"])
        result2 = execute_command(["xrange", "stream", "1-0", "1-0"])
        result3 = execute_command(["XrAnGe", "stream", "1-0", "1-0"])

        assert result1 == result2 == result3

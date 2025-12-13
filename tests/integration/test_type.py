"""Integration tests for TYPE command."""

import pytest

from tests.helpers import execute_command


class TestTypeIntegration:
    """Test TYPE command with real storage."""

    def test_type_string_key(self):
        """TYPE returns 'string' for SET keys."""
        execute_command(["SET", "mykey", "value"])
        result = execute_command(["TYPE", "mykey"])

        assert result == "string"

    def test_type_list_key(self):
        """TYPE returns 'list' for RPUSH keys."""
        execute_command(["RPUSH", "mylist", "item"])
        result = execute_command(["TYPE", "mylist"])

        assert result == "list"

    def test_type_nonexistent_key(self):
        """TYPE returns 'none' for non-existent keys."""
        result = execute_command(["TYPE", "nonexistent"])

        assert result == "none"

    def test_type_after_lpush(self):
        """TYPE returns 'list' after LPUSH."""
        execute_command(["LPUSH", "mylist", "a", "b", "c"])
        result = execute_command(["TYPE", "mylist"])

        assert result == "list"

    def test_type_multiple_keys_different_types(self):
        """TYPE correctly identifies different key types."""
        execute_command(["SET", "str_key", "hello"])
        execute_command(["RPUSH", "list_key", "world"])

        assert execute_command(["TYPE", "str_key"]) == "string"
        assert execute_command(["TYPE", "list_key"]) == "list"
        assert execute_command(["TYPE", "no_key"]) == "none"

    def test_type_after_key_deletion(self):
        """TYPE returns 'none' after key is implicitly deleted."""
        execute_command(["RPUSH", "mylist", "a"])
        execute_command(["LPOP", "mylist", "1"])
        # List is now empty and should be deleted
        result = execute_command(["TYPE", "mylist"])

        assert result == "none"

    def test_type_after_set_overwrites_list(self):
        """TYPE changes from 'list' to 'string' when SET overwrites."""
        execute_command(["RPUSH", "mykey", "item"])
        assert execute_command(["TYPE", "mykey"]) == "list"

        execute_command(["SET", "mykey", "string_value"])
        assert execute_command(["TYPE", "mykey"]) == "string"

    def test_type_case_insensitive(self):
        """TYPE command is case-insensitive."""
        execute_command(["SET", "mykey", "value"])

        result1 = execute_command(["TYPE", "mykey"])
        result2 = execute_command(["type", "mykey"])
        result3 = execute_command(["TyPe", "mykey"])

        assert result1 == result2 == result3 == "string"

    def test_type_returns_bulk_string_in_resp(self):
        """TYPE returns bulk string in RESP format."""
        execute_command(["SET", "key", "value"])
        result = execute_command(["TYPE", "key"])

        # Verify it's a string
        assert isinstance(result, str)

        # Verify RESP encoding
        from app.resp import RESPEncoder

        response = RESPEncoder.encode(result)
        assert response == b"$6\r\nstring\r\n"  # Bulk string "string"


class TestTypeErrors:
    """Test TYPE error handling."""

    def test_type_no_args(self):
        """TYPE without args raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["TYPE"])

    def test_type_too_many_args(self):
        """TYPE with multiple keys raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["TYPE", "key1", "key2"])

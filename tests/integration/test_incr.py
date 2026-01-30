"""Integration tests for INCR command."""

import pytest

from app.storage import get_storage, reset_storage


@pytest.fixture(autouse=True)
def clean_storage():
    """Reset storage before each test."""
    reset_storage()
    yield
    reset_storage()


class TestIncrIntegration:
    """Integration tests for INCR command with real storage."""

    def test_incr_nonexistent_key(self):
        """INCR on nonexistent key sets it to 1."""
        storage = get_storage()
        result = storage.incr("counter")
        
        assert result == 1
        assert storage.get("counter") == "1"

    def test_incr_existing_value(self):
        """INCR increments existing integer value."""
        storage = get_storage()
        storage.set("counter", "5")
        
        result = storage.incr("counter")
        
        assert result == 6
        assert storage.get("counter") == "6"

    def test_incr_multiple_times(self):
        """INCR can be called multiple times."""
        storage = get_storage()
        
        assert storage.incr("counter") == 1
        assert storage.incr("counter") == 2
        assert storage.incr("counter") == 3
        assert storage.get("counter") == "3"

    def test_incr_negative_value(self):
        """INCR can increment negative values."""
        storage = get_storage()
        storage.set("counter", "-5")
        
        result = storage.incr("counter")
        
        assert result == -4
        assert storage.get("counter") == "-4"

    def test_incr_zero(self):
        """INCR increments zero to one."""
        storage = get_storage()
        storage.set("counter", "0")
        
        result = storage.incr("counter")
        
        assert result == 1
        assert storage.get("counter") == "1"

    def test_incr_non_integer_value_error(self):
        """INCR raises error for non-integer string."""
        storage = get_storage()
        storage.set("text", "hello")
        
        with pytest.raises(ValueError, match="value is not an integer or out of range"):
            storage.incr("text")

    def test_incr_float_value_error(self):
        """INCR raises error for float string."""
        storage = get_storage()
        storage.set("float", "3.14")
        
        with pytest.raises(ValueError, match="value is not an integer or out of range"):
            storage.incr("float")

    def test_incr_empty_string_error(self):
        """INCR raises error for empty string."""
        storage = get_storage()
        storage.set("empty", "")
        
        with pytest.raises(ValueError, match="value is not an integer or out of range"):
            storage.incr("empty")

    def test_incr_whitespace_error(self):
        """INCR raises error for whitespace."""
        storage = get_storage()
        storage.set("whitespace", "  ")
        
        with pytest.raises(ValueError, match="value is not an integer or out of range"):
            storage.incr("whitespace")

    def test_incr_wrong_type_error(self):
        """INCR raises error when key holds a list."""
        from app.exceptions import WrongTypeError
        
        storage = get_storage()
        storage.lpush("mylist", "a", "b", "c")
        
        with pytest.raises(WrongTypeError):
            storage.incr("mylist")

    def test_incr_large_number(self):
        """INCR works with large numbers."""
        storage = get_storage()
        storage.set("bignum", "999999999999")
        
        result = storage.incr("bignum")
        
        assert result == 1000000000000
        assert storage.get("bignum") == "1000000000000"

    def test_incr_preserves_string_type(self):
        """INCR keeps value as string in storage."""
        storage = get_storage()
        storage.incr("counter")
        
        # Value should be stored as string
        value = storage.get("counter")
        assert isinstance(value, str)
        assert value == "1"

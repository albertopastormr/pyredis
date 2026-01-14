"""Unit tests for XADD entry ID validation."""

import pytest

from app.storage.types import RedisStream


class TestStreamEntryIdValidation:
    """Test entry ID validation in RedisStream."""

    def test_parse_valid_id(self):
        """Parse a valid entry ID."""
        stream = RedisStream()
        ms_time, seq_num = stream._parse_entry_id("1526985054069-0")
        assert ms_time == 1526985054069
        assert seq_num == 0

    def test_parse_id_with_different_values(self):
        """Parse various valid IDs."""
        stream = RedisStream()
        
        ms_time, seq_num = stream._parse_entry_id("0-1")
        assert ms_time == 0
        assert seq_num == 1
        
        ms_time, seq_num = stream._parse_entry_id("123-456")
        assert ms_time == 123
        assert seq_num == 456

    def test_parse_invalid_id_no_dash(self):
        """Invalid ID without dash raises error."""
        stream = RedisStream()
        with pytest.raises(ValueError, match="Invalid stream ID"):
            stream._parse_entry_id("12345")

    def test_parse_invalid_id_too_many_parts(self):
        """Invalid ID with too many parts raises error."""
        stream = RedisStream()
        with pytest.raises(ValueError, match="Invalid stream ID"):
            stream._parse_entry_id("123-456-789")

    def test_parse_invalid_id_non_numeric(self):
        """Invalid ID with non-numeric parts raises error."""
        stream = RedisStream()
        with pytest.raises(ValueError, match="Invalid stream ID"):
            stream._parse_entry_id("abc-def")

    def test_parse_invalid_id_negative_values(self):
        """Invalid ID with negative values raises error."""
        stream = RedisStream()
        with pytest.raises(ValueError, match="Invalid stream ID"):
            stream._parse_entry_id("-1-0")
        
        with pytest.raises(ValueError, match="Invalid stream ID"):
            stream._parse_entry_id("0--1")

    def test_xadd_first_entry_minimum_id(self):
        """First entry must be greater than 0-0."""
        stream = RedisStream()
        
        # 0-0 should fail
        with pytest.raises(ValueError, match="must be greater than 0-0"):
            stream.xadd("0-0", {"field": "value"})

    def test_xadd_first_entry_valid_minimum(self):
        """First entry 0-1 is valid."""
        stream = RedisStream()
        result = stream.xadd("0-1", {"field": "value"})
        assert result == "0-1"
        assert len(stream.entries) == 1

    def test_xadd_first_entry_any_valid_id(self):
        """First entry can be any ID > 0-0."""
        stream = RedisStream()
        result = stream.xadd("1526985054069-0", {"temp": "36"})
        assert result == "1526985054069-0"

    def test_xadd_second_entry_must_be_greater(self):
        """Second entry ID must be greater than first."""
        stream = RedisStream()
        stream.xadd("100-5", {"field": "value1"})
        
        # Same ID should fail
        with pytest.raises(ValueError, match="equal or smaller"):
            stream.xadd("100-5", {"field": "value2"})

    def test_xadd_second_entry_smaller_timestamp_fails(self):
        """Second entry with smaller timestamp fails."""
        stream = RedisStream()
        stream.xadd("100-5", {"field": "value1"})
        
        with pytest.raises(ValueError, match="equal or smaller"):
            stream.xadd("99-10", {"field": "value2"})

    def test_xadd_second_entry_same_timestamp_smaller_sequence_fails(self):
        """Second entry with same timestamp but smaller sequence fails."""
        stream = RedisStream()
        stream.xadd("100-5", {"field": "value1"})
        
        with pytest.raises(ValueError, match="equal or smaller"):
            stream.xadd("100-4", {"field": "value2"})

    def test_xadd_second_entry_same_timestamp_equal_sequence_fails(self):
        """Second entry with same timestamp and sequence fails."""
        stream = RedisStream()
        stream.xadd("100-5", {"field": "value1"})
        
        with pytest.raises(ValueError, match="equal or smaller"):
            stream.xadd("100-5", {"field": "value2"})

    def test_xadd_second_entry_same_timestamp_greater_sequence_succeeds(self):
        """Second entry with same timestamp but greater sequence succeeds."""
        stream = RedisStream()
        stream.xadd("100-5", {"field": "value1"})
        result = stream.xadd("100-6", {"field": "value2"})
        
        assert result == "100-6"
        assert len(stream.entries) == 2

    def test_xadd_second_entry_greater_timestamp_succeeds(self):
        """Second entry with greater timestamp succeeds."""
        stream = RedisStream()
        stream.xadd("100-5", {"field": "value1"})
        result = stream.xadd("101-0", {"field": "value2"})
        
        assert result == "101-0"
        assert len(stream.entries) == 2

    def test_xadd_multiple_entries_incremental(self):
        """Multiple entries with incremental IDs."""
        stream = RedisStream()
        
        stream.xadd("0-1", {"a": "1"})
        stream.xadd("0-2", {"a": "2"})
        stream.xadd("1-0", {"a": "3"})
        stream.xadd("1-1", {"a": "4"})
        stream.xadd("100-0", {"a": "5"})
        
        assert len(stream.entries) == 5

    def test_xadd_invalid_id_format(self):
        """Invalid ID format raises error."""
        stream = RedisStream()
        
        with pytest.raises(ValueError, match="Invalid stream ID"):
            stream.xadd("invalid", {"field": "value"})

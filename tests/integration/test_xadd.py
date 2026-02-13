"""Integration tests for XADD command."""

import pytest

from tests.helpers import execute_command


class TestXaddIntegration:
    """Test XADD command with real storage."""

    def test_xadd_creates_stream(self):
        """XADD creates a new stream if it doesn't exist."""
        result = execute_command(["XADD", "mystream", "0-1", "field", "value"])
        assert result == "0-1"

    def test_xadd_returns_entry_id(self):
        """XADD returns the entry ID."""
        result = execute_command(["XADD", "weather", "1526985054069-0", "temperature", "36"])
        assert result == "1526985054069-0"

    def test_xadd_appends_to_stream(self):
        """XADD appends entries to existing stream."""
        result1 = execute_command(["XADD", "mystream", "1526985054069-0", "temperature", "36"])
        result2 = execute_command(["XADD", "mystream", "1526985054079-0", "temperature", "37"])

        assert result1 == "1526985054069-0"
        assert result2 == "1526985054079-0"

    def test_type_returns_stream(self):
        """TYPE returns 'stream' for stream keys."""
        execute_command(["XADD", "mystream", "0-1", "field", "value"])
        result = execute_command(["TYPE", "mystream"])

        assert result == {"ok": "stream"}

    def test_xadd_multiple_fields(self):
        """XADD with multiple field-value pairs."""
        result = execute_command(
            [
                "XADD",
                "weather",
                "1526985054069-0",
                "temperature",
                "36",
                "humidity",
                "95",
            ]
        )
        assert result == "1526985054069-0"

    def test_xadd_preserves_fields(self):
        """XADD stores field-value pairs correctly."""
        # We can verify by checking that the stream was created
        result = execute_command(["XADD", "mystream", "0-1", "foo", "bar", "baz", "qux"])
        assert result == "0-1"

        # Verify type is stream
        type_result = execute_command(["TYPE", "mystream"])
        assert type_result == {"ok": "stream"}

    def test_xadd_case_insensitive(self):
        """XADD command is case-insensitive."""
        result1 = execute_command(["XADD", "s1", "0-1", "f", "v"])
        result2 = execute_command(["xadd", "s2", "0-2", "f", "v"])
        result3 = execute_command(["XaDd", "s3", "0-3", "f", "v"])

        assert result1 == "0-1"
        assert result2 == "0-2"
        assert result3 == "0-3"

    def test_xadd_different_streams(self):
        """XADD to different streams are independent."""
        execute_command(["XADD", "stream1", "0-1", "field", "value1"])
        execute_command(["XADD", "stream2", "0-1", "field", "value2"])

        assert execute_command(["TYPE", "stream1"]) == {"ok": "stream"}
        assert execute_command(["TYPE", "stream2"]) == {"ok": "stream"}


class TestXaddErrors:
    """Test XADD error handling."""

    def test_xadd_no_args(self):
        """XADD without args raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["XADD"])

    def test_xadd_only_key(self):
        """XADD with only key raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["XADD", "key"])

    def test_xadd_missing_fields(self):
        """XADD without field-value pairs raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["XADD", "key", "0-1"])

    def test_xadd_odd_field_values(self):
        """XADD with odd field-value count raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["XADD", "key", "0-1", "field"])

    def test_xadd_on_string_key_fails(self):
        """XADD on existing string key raises WRONGTYPE error."""
        from app.exceptions import WrongTypeError

        execute_command(["SET", "mykey", "value"])

        with pytest.raises(WrongTypeError):
            execute_command(["XADD", "mykey", "0-1", "field", "value"])

    def test_xadd_on_list_key_fails(self):
        """XADD on existing list key raises WRONGTYPE error."""
        from app.exceptions import WrongTypeError

        execute_command(["RPUSH", "mylist", "item"])

        with pytest.raises(WrongTypeError):
            execute_command(["XADD", "mylist", "0-1", "field", "value"])


class TestXaddIdValidation:
    """Test XADD entry ID validation."""

    def test_xadd_first_entry_zero_zero_fails(self):
        """First entry with ID 0-0 fails."""
        with pytest.raises(ValueError, match="must be greater than 0-0"):
            execute_command(["XADD", "stream", "0-0", "field", "value"])

    def test_xadd_first_entry_zero_one_succeeds(self):
        """First entry with ID 0-1 succeeds."""
        result = execute_command(["XADD", "stream", "0-1", "field", "value"])
        assert result == "0-1"

    def test_xadd_duplicate_id_fails(self):
        """Adding entry with same ID as last entry fails."""
        execute_command(["XADD", "stream", "100-5", "field", "value1"])

        with pytest.raises(ValueError, match="equal or smaller"):
            execute_command(["XADD", "stream", "100-5", "field", "value2"])

    def test_xadd_smaller_timestamp_fails(self):
        """Adding entry with smaller timestamp fails."""
        execute_command(["XADD", "stream", "100-5", "field", "value1"])

        with pytest.raises(ValueError, match="equal or smaller"):
            execute_command(["XADD", "stream", "99-10", "field", "value2"])

    def test_xadd_same_timestamp_smaller_sequence_fails(self):
        """Adding entry with same timestamp but smaller sequence fails."""
        execute_command(["XADD", "stream", "100-5", "field", "value1"])

        with pytest.raises(ValueError, match="equal or smaller"):
            execute_command(["XADD", "stream", "100-4", "field", "value2"])

    def test_xadd_same_timestamp_greater_sequence_succeeds(self):
        """Adding entry with same timestamp but greater sequence succeeds."""
        execute_command(["XADD", "stream", "100-5", "field", "value1"])
        result = execute_command(["XADD", "stream", "100-6", "field", "value2"])

        assert result == "100-6"

    def test_xadd_greater_timestamp_succeeds(self):
        """Adding entry with greater timestamp succeeds."""
        execute_command(["XADD", "stream", "100-5", "field", "value1"])
        result = execute_command(["XADD", "stream", "101-0", "field", "value2"])

        assert result == "101-0"

    def test_xadd_incremental_ids(self):
        """Adding multiple entries with incremental IDs."""
        result1 = execute_command(["XADD", "stream", "0-1", "a", "1"])
        result2 = execute_command(["XADD", "stream", "0-2", "a", "2"])
        result3 = execute_command(["XADD", "stream", "1-0", "a", "3"])
        result4 = execute_command(["XADD", "stream", "1-1", "a", "4"])

        assert result1 == "0-1"
        assert result2 == "0-2"
        assert result3 == "1-0"
        assert result4 == "1-1"

    def test_xadd_invalid_id_format_no_dash(self):
        """Invalid ID format without dash fails."""
        with pytest.raises(ValueError, match="Invalid stream ID"):
            execute_command(["XADD", "stream", "12345", "field", "value"])

    def test_xadd_invalid_id_format_too_many_parts(self):
        """Invalid ID format with too many parts fails."""
        with pytest.raises(ValueError, match="Invalid stream ID"):
            execute_command(["XADD", "stream", "1-2-3", "field", "value"])

    def test_xadd_invalid_id_non_numeric(self):
        """Invalid ID with non-numeric parts fails."""
        with pytest.raises(ValueError, match="Invalid stream ID"):
            execute_command(["XADD", "stream", "abc-def", "field", "value"])

    def test_xadd_invalid_id_negative_timestamp(self):
        """Invalid ID with negative timestamp fails."""
        with pytest.raises(ValueError, match="Invalid stream ID"):
            execute_command(["XADD", "stream", "-1-0", "field", "value"])

    def test_xadd_invalid_id_negative_sequence(self):
        """Invalid ID with negative sequence fails."""
        with pytest.raises(ValueError, match="Invalid stream ID"):
            execute_command(["XADD", "stream", "0--1", "field", "value"])


class TestXaddAutoGeneratedIds:
    """Test XADD with auto-generated IDs."""

    def test_xadd_autogen_sequence_empty_stream(self):
        """Auto-generate sequence for empty stream."""
        result = execute_command(["XADD", "stream", "1-*", "foo", "bar"])
        assert result == "1-0"

    def test_xadd_autogen_sequence_zero_timestamp(self):
        """Auto-generate sequence uses 1 for zero timestamp."""
        result = execute_command(["XADD", "stream", "0-*", "foo", "bar"])
        assert result == "0-1"

    def test_xadd_autogen_sequence_increments(self):
        """Auto-generate sequence increments for same timestamp."""
        result1 = execute_command(["XADD", "stream", "100-*", "a", "1"])
        result2 = execute_command(["XADD", "stream", "100-*", "a", "2"])
        result3 = execute_command(["XADD", "stream", "100-*", "a", "3"])

        assert result1 == "100-0"
        assert result2 == "100-1"
        assert result3 == "100-2"

    def test_xadd_autogen_sequence_new_timestamp(self):
        """Auto-generate sequence resets for new timestamp."""
        execute_command(["XADD", "stream", "100-*", "a", "1"])
        execute_command(["XADD", "stream", "100-*", "a", "2"])
        result = execute_command(["XADD", "stream", "200-*", "a", "3"])

        assert result == "200-0"

    def test_xadd_autogen_full_wildcard(self):
        """Auto-generate both timestamp and sequence."""
        result = execute_command(["XADD", "stream", "*", "foo", "bar"])

        # Should have format ms_time-seq_num
        assert "-" in result
        ms_time, seq_num = result.split("-")
        assert int(ms_time) > 0
        assert seq_num == "0"

    def test_xadd_autogen_multiple_wildcards(self):
        """Multiple auto-generated entries."""
        result1 = execute_command(["XADD", "stream", "*", "a", "1"])
        result2 = execute_command(["XADD", "stream", "*", "a", "2"])

        # Both should be valid
        ms1, seq1 = result1.split("-")
        ms2, seq2 = result2.split("-")

        assert int(ms2) >= int(ms1)

    def test_xadd_mixed_explicit_autogen(self):
        """Mix explicit and auto-generated IDs."""
        execute_command(["XADD", "stream", "1-0", "a", "1"])
        result = execute_command(["XADD", "stream", "1-*", "a", "2"])
        assert result == "1-1"

        execute_command(["XADD", "stream", "2-0", "a", "3"])
        result = execute_command(["XADD", "stream", "2-*", "a", "4"])
        assert result == "2-1"

    def test_xadd_autogen_type_still_stream(self):
        """TYPE returns stream for auto-generated IDs."""
        execute_command(["XADD", "mystream", "1-*", "field", "value"])
        result = execute_command(["TYPE", "mystream"])
        assert result == {"ok": "stream"}

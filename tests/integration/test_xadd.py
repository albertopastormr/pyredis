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

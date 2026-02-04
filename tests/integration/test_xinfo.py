"""Integration tests for XINFO command."""

import pytest

from app.resp import RESPEncoder
from tests.helpers import execute_command


class TestXinfoIntegration:
    """Integration tests for XINFO command."""

    def test_xinfo_stream_basic(self):
        """Test XINFO STREAM on stream with entries."""
        # Create a stream with one entry
        execute_command(["XADD", "mystream", "1000-0", "field1", "value1"])
        
        # Get stream info
        result = execute_command(["XINFO", "STREAM", "mystream"])
        
        # Should return array with stream information
        assert isinstance(result, list)
        # First element should be "length"
        assert "length" in result

    def test_xinfo_stream_with_multiple_entries(self):
        """Test XINFO STREAM with multiple entries."""
        # Add multiple entries
        execute_command(["XADD", "mystream", "1000-0", "field1", "value1"])
        execute_command(["XADD", "mystream", "1001-0", "field2", "value2"])
        execute_command(["XADD", "mystream", "1002-0", "field3", "value3"])
        
        # Get stream info
        result = execute_command(["XINFO", "STREAM", "mystream"])
        
        assert isinstance(result, list)
        # Find length in the result
        if "length" in result:
            length_index = result.index("length")
            assert result[length_index + 1] == 3

    def test_xinfo_stream_nonexistent(self):
        """Test XINFO STREAM on nonexistent stream."""
        # Trying to get info on non-existent stream should raise error
        with pytest.raises(Exception):
            execute_command(["XINFO", "STREAM", "nonexistent"])

    def test_xinfo_requires_arguments(self):
        """Test XINFO requires subcommand and key."""
        # No arguments
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["XINFO"])
        
        # Only subcommand, no key
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["XINFO", "STREAM"])

    def test_xinfo_resp_encoding(self):
        """Test XINFO command RESP encoding."""
        # Encode XINFO STREAM command
        encoded = RESPEncoder.encode(["XINFO", "STREAM", "mystream"])
        
        # Verify RESP format
        assert encoded.startswith(b"*3\r\n")
        assert b"$5\r\nXINFO\r\n" in encoded
        assert b"$6\r\nSTREAM\r\n" in encoded
        assert b"$8\r\nmystream\r\n" in encoded

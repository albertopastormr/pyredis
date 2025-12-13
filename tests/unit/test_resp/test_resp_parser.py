"""Tests for RESP protocol parser and encoder."""

from app.resp import RESPEncoder, RESPParser


class TestRESPParser:
    """Test RESP protocol parsing."""

    def test_parse_simple_string(self):
        """Test parsing simple strings."""
        data = b"+OK\r\n"
        assert RESPParser.parse(data) == "OK"

    def test_parse_bulk_string(self):
        """Test parsing bulk strings."""
        data = b"$5\r\nhello\r\n"
        assert RESPParser.parse(data) == "hello"

    def test_parse_bulk_string_empty(self):
        """Test parsing empty bulk strings."""
        data = b"$0\r\n\r\n"
        assert RESPParser.parse(data) == ""

    def test_parse_null_bulk_string(self):
        """Test parsing null bulk strings."""
        data = b"$-1\r\n"
        assert RESPParser.parse(data) is None

    def test_parse_integer(self):
        """Test parsing integers."""
        data = b":42\r\n"
        assert RESPParser.parse(data) == 42

    def test_parse_array(self):
        """Test parsing arrays."""
        data = b"*2\r\n$4\r\nECHO\r\n$3\r\nhey\r\n"
        assert RESPParser.parse(data) == ["ECHO", "hey"]

    def test_parse_empty_array(self):
        """Test parsing empty arrays."""
        data = b"*0\r\n"
        assert RESPParser.parse(data) == []

    def test_parse_ping_command(self):
        """Test parsing PING command."""
        data = b"*1\r\n$4\r\nPING\r\n"
        assert RESPParser.parse(data) == ["PING"]

    def test_parse_echo_command(self):
        """Test parsing ECHO command."""
        data = b"*2\r\n$4\r\nECHO\r\n$13\r\nHello, Redis!\r\n"
        assert RESPParser.parse(data) == ["ECHO", "Hello, Redis!"]

    def test_parse_error(self):
        """Test parsing errors."""
        data = b"-ERR unknown command\r\n"
        assert RESPParser.parse(data) == "ERR unknown command"


class TestRESPEncoder:
    """Test RESP protocol encoding."""

    def test_encode_simple_string(self):
        """Test encoding simple strings via dict."""
        result = RESPEncoder.encode({"ok": "PONG"})
        assert result == b"+PONG\r\n"

    def test_encode_bulk_string(self):
        """Test encoding bulk strings."""
        result = RESPEncoder.encode("hello")
        assert result == b"$5\r\nhello\r\n"

    def test_encode_bulk_string_empty(self):
        """Test encoding empty strings."""
        result = RESPEncoder.encode("")
        assert result == b"$0\r\n\r\n"

    def test_encode_null(self):
        """Test encoding None as null bulk string (for GET, etc)."""
        result = RESPEncoder.encode(None)
        assert result == b"$-1\r\n"

    def test_encode_integer(self):
        """Test encoding integers."""
        result = RESPEncoder.encode(42)
        assert result == b":42\r\n"

    def test_encode_error(self):
        """Test encoding errors via dict."""
        result = RESPEncoder.encode({"error": "ERR something went wrong"})
        assert result == b"-ERR something went wrong\r\n"

    def test_encode_array(self):
        """Test encoding arrays."""
        result = RESPEncoder.encode(["ECHO", "hey"])
        assert result == b"*2\r\n$4\r\nECHO\r\n$3\r\nhey\r\n"

    def test_encode_empty_array(self):
        """Test encoding empty arrays."""
        result = RESPEncoder.encode([])
        assert result == b"*0\r\n"

    def test_encode_nested_array(self):
        """Test encoding nested arrays."""
        result = RESPEncoder.encode(["GET", ["key1", "key2"]])
        expected = b"*2\r\n$3\r\nGET\r\n*2\r\n$4\r\nkey1\r\n$4\r\nkey2\r\n"
        assert result == expected


class TestRoundTrip:
    """Test encoding then parsing gives back original value."""

    def test_roundtrip_string(self):
        """Test string round trip."""
        original = "hello"
        encoded = RESPEncoder.encode(original)
        decoded = RESPParser.parse(encoded)
        assert decoded == original

    def test_roundtrip_integer(self):
        """Test integer round trip."""
        original = 42
        encoded = RESPEncoder.encode(original)
        decoded = RESPParser.parse(encoded)
        assert decoded == original

    def test_roundtrip_array(self):
        """Test array round trip."""
        original = ["ECHO", "hello", "world"]
        encoded = RESPEncoder.encode(original)
        decoded = RESPParser.parse(encoded)
        assert decoded == original

    def test_roundtrip_null(self):
        """Test null round trip."""
        original = None
        encoded = RESPEncoder.encode(original)
        decoded = RESPParser.parse(encoded)
        assert decoded == original

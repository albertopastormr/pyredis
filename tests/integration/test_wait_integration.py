"""Integration test for WAIT command."""

from app.resp import RESPEncoder, RESPParser


class TestWaitIntegration:
    """Integration tests for WAIT command."""

    def test_wait_command_encoding(self):
        """Verify WAIT command encodes correctly."""
        # WAIT 3 5000
        encoded = RESPEncoder.encode(["WAIT", "3", "5000"])

        # Verify RESP format
        assert encoded == b"*3\r\n$4\r\nWAIT\r\n$1\r\n3\r\n$4\r\n5000\r\n"

    def test_wait_response_encoding(self):
        """Verify WAIT response (integer) encodes correctly."""
        # Response: 0
        encoded = RESPEncoder.encode(0)
        assert encoded == b":0\r\n"

        # Response: 2
        encoded = RESPEncoder.encode(2)
        assert encoded == b":2\r\n"

        # Response: 3
        encoded = RESPEncoder.encode(3)
        assert encoded == b":3\r\n"

        # Response: 1000
        encoded = RESPEncoder.encode(1000)
        assert encoded == b":1000\r\n"

        # Response: -5 (negative integer with sign)
        encoded = RESPEncoder.encode(-5)
        assert encoded == b":-5\r\n"

    def test_wait_command_parsing(self):
        """Verify WAIT command can be parsed correctly."""
        raw_data = b"*3\r\n$4\r\nWAIT\r\n$3\r\n100\r\n$4\r\n5000\r\n"

        command = RESPParser.parse(raw_data)

        assert isinstance(command, list)
        assert len(command) == 3
        assert command[0].upper() == "WAIT"
        assert command[1] == "100"
        assert command[2] == "5000"

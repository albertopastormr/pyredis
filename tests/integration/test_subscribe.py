"""Integration tests for the SUBSCRIBE command."""

from app.resp import RESPEncoder, RESPParser
from tests.helpers import execute_command


class TestSubscribeIntegration:
    """Test SUBSCRIBE command full flow."""

    def test_subscribe_command_format(self):
        """Test that SUBSCRIBE command returns the exact expected RESP format."""

        # Send SUBSCRIBE cmd
        request = b"*2\r\n$9\r\nSUBSCRIBE\r\n$3\r\nfoo\r\n"

        # Parse
        command = RESPParser.parse(request)
        assert command == ["SUBSCRIBE", "foo"]

        # Check full exact match based on the project description
        expected_response = b"*3\r\n$9\r\nsubscribe\r\n$3\r\nfoo\r\n:1\r\n"

        result = execute_command(command)
        actual_response = RESPEncoder.encode(result)

        assert actual_response == expected_response

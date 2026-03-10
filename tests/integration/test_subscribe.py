"""Integration tests for the SUBSCRIBE command."""

from app.pubsub import remove_pubsub_context
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

        result = execute_command(command, connection_id="test_client_1")
        actual_response = RESPEncoder.encode(result)

        assert actual_response == expected_response
        remove_pubsub_context("test_client_1")

    def test_multiple_subscribe_commands(self):
        """Test that multiple SUBSCRIBE commands increment the channel count correctly."""
        client_id = "test_client_2"

        # First subscription
        cmd1 = ["SUBSCRIBE", "foo"]
        res1 = execute_command(cmd1, connection_id=client_id)
        assert res1 == ["subscribe", "foo", 1]

        # Second distinct subscription
        cmd2 = ["SUBSCRIBE", "bar"]
        res2 = execute_command(cmd2, connection_id=client_id)
        assert res2 == ["subscribe", "bar", 2]

        # Duplicate subscription (count remains same)
        cmd3 = ["SUBSCRIBE", "bar"]
        res3 = execute_command(cmd3, connection_id=client_id)
        assert res3 == ["subscribe", "bar", 2]

        remove_pubsub_context(client_id)

    def test_per_client_subscription_tracking(self):
        """Test that subscription counts are tracked per client independently."""
        client_a = "client_A"
        client_b = "client_B"

        # Client A subscribes
        res_a1 = execute_command(["SUBSCRIBE", "chan1"], connection_id=client_a)
        assert res_a1 == ["subscribe", "chan1", 1]

        # Client B subscribes
        res_b1 = execute_command(["SUBSCRIBE", "chan2"], connection_id=client_b)
        assert res_b1 == ["subscribe", "chan2", 1]

        # Client A subscribes to another
        res_a2 = execute_command(["SUBSCRIBE", "chan2"], connection_id=client_a)
        assert res_a2 == ["subscribe", "chan2", 2]

        # Clean up
        remove_pubsub_context(client_a)
        remove_pubsub_context(client_b)

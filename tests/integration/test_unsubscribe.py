"""Integration tests for the UNSUBSCRIBE command."""

from app.pubsub import remove_pubsub_context
from tests.helpers import execute_command, execute_command_with_mock_writer


class TestUnsubscribeIntegration:
    """Test UNSUBSCRIBE command behavior."""

    def test_unsubscribe_removes_channels(self):
        """Test that UNSUBSCRIBE effectively removes a client's specific channel mapping arrays and blocking further PUBLISH messages natively."""
        from app.resp import RESPEncoder

        client_u = "unsub_client_u"
        publisher = "unsub_publisher"

        try:
            # Setup initial state
            # client_u subscribes to 'alpha' and 'beta'
            res_sub_alpha, writer_u = execute_command_with_mock_writer(
                ["SUBSCRIBE", "alpha"], connection_id=client_u
            )
            assert res_sub_alpha == ["subscribe", "alpha", 1]

            res_sub_beta, _ = execute_command_with_mock_writer(
                ["SUBSCRIBE", "beta"], connection_id=client_u
            )
            assert res_sub_beta == ["subscribe", "beta", 2]

            # Ensure mock state is clean
            writer_u.write.reset_mock()

            # Prove subscription is valid first
            res_pub = execute_command(["PUBLISH", "alpha", "initial"], connection_id=publisher)
            assert res_pub == 1

            expected_payload = RESPEncoder.encode(["message", "alpha", "initial"])
            writer_u.write.assert_called_once_with(expected_payload)
            writer_u.drain.assert_awaited_once()

            writer_u.write.reset_mock()

            # Execute UNSUBSCRIBE manually against 'alpha'
            res_unsub = execute_command(["UNSUBSCRIBE", "alpha"], connection_id=client_u)
            assert res_unsub == ["unsubscribe", "alpha", 1]  # 1 channel remaining ('beta')

            # Prove PUBLISH to 'alpha' no longer delivers
            res_pub_alpha = execute_command(
                ["PUBLISH", "alpha", "after_unsub"], connection_id=publisher
            )
            assert res_pub_alpha == 0
            writer_u.write.assert_not_called()

            # Prove PUBLISH to 'beta' STILL delivers correctly
            res_pub_beta = execute_command(
                ["PUBLISH", "beta", "still subscribed"], connection_id=publisher
            )
            assert res_pub_beta == 1
            expected_beta = RESPEncoder.encode(["message", "beta", "still subscribed"])
            writer_u.write.assert_called_once_with(expected_beta)

            # Unsubscribe from 'beta' and reach 0 internally
            res_unsub_beta = execute_command(["UNSUBSCRIBE", "beta"], connection_id=client_u)
            assert res_unsub_beta == ["unsubscribe", "beta", 0]

            # Attempt to unsubscribe from an unbound channel 'gamma'
            res_unsub_gamma = execute_command(["UNSUBSCRIBE", "gamma"], connection_id=client_u)
            assert res_unsub_gamma == ["unsubscribe", "gamma", 0]

            # Edge case test: UNSUBSCRIBE multiple explicitly
            # resend dummy subscriptions
            execute_command(["SUBSCRIBE", "x"], connection_id=client_u)
            execute_command(["SUBSCRIBE", "y"], connection_id=client_u)

            # If multiple are passed, our logic iterates and produces a list
            res_multi = execute_command(["UNSUBSCRIBE", "x", "y"], connection_id=client_u)

            assert res_multi == [["unsubscribe", "x", 1], ["unsubscribe", "y", 0]]

        finally:
            remove_pubsub_context(client_u)
            remove_pubsub_context(publisher)

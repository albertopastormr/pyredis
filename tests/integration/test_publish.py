"""Integration tests for the PUBLISH command."""

from app.pubsub import remove_pubsub_context
from tests.helpers import execute_command


class TestPublishIntegration:
    """Test PUBLISH command."""

    def test_publish_returns_subscriber_count(self):
        """Test that PUBLISH returns the exact number of subscribed clients."""
        client_a = "pub_client_a"
        client_b = "pub_client_b"
        client_c = "pub_client_c"

        try:
            from tests.helpers import execute_command_with_mock_writer

            # Setup subscriptions
            # client_a -> 'foo'
            res_a, _ = execute_command_with_mock_writer(
                ["SUBSCRIBE", "foo"], connection_id=client_a
            )
            assert res_a == ["subscribe", "foo", 1]

            # client_b -> 'bar'
            res_b, _ = execute_command_with_mock_writer(
                ["SUBSCRIBE", "bar"], connection_id=client_b
            )
            assert res_b == ["subscribe", "bar", 1]

            # client_c -> 'bar'
            res_c, _ = execute_command_with_mock_writer(
                ["SUBSCRIBE", "bar"], connection_id=client_c
            )
            assert res_c == ["subscribe", "bar", 1]

            # We use a distinct client (or no client) for PUBLISH evaluation
            # PUBLISH 'bar' (Expected: 2 subscribers)
            res_pub_bar = execute_command(
                ["PUBLISH", "bar", "msg"], connection_id="some_other_client"
            )
            assert res_pub_bar == 2

            # PUBLISH 'foo' (Expected: 1 subscriber)
            res_pub_foo = execute_command(
                ["PUBLISH", "foo", "msg"], connection_id="some_other_client"
            )
            assert res_pub_foo == 1

            # PUBLISH 'unknown' (Expected: 0 subscribers)
            res_pub_unknown = execute_command(
                ["PUBLISH", "unknown", "msg"], connection_id="some_other_client"
            )
            assert res_pub_unknown == 0

        finally:
            remove_pubsub_context(client_a)
            remove_pubsub_context(client_b)
            remove_pubsub_context(client_c)
            remove_pubsub_context("some_other_client")

    def test_publish_delivers_messages(self):
        """Test that PUBLISH effectively routes exactly matching string arrays iteratively to valid TCP connections dynamically."""
        import app.pubsub
        from tests.helpers import execute_command_with_mock_writer

        client_d = "pub_listener_d"
        client_e = "pub_listener_e"

        try:
            # 1. Provide mock writers safely
            # client_d subscribes to "route_test"
            _, writer_d = execute_command_with_mock_writer(
                ["SUBSCRIBE", "route_test"], connection_id=client_d
            )

            # client_e subscribes to "other_route"
            _, writer_e = execute_command_with_mock_writer(
                ["SUBSCRIBE", "other_route"], connection_id=client_e
            )

            # Reset mock states tracking natively prior to test
            writer_d.write.reset_mock()
            writer_e.write.reset_mock()

            # 2. Fire PUBLISH manually
            from app.resp import RESPEncoder

            res_publish = execute_command(
                ["PUBLISH", "route_test", "SecretData!"], connection_id="publisher"
            )

            # Expecting exactly 1 subscriber (client_d)
            assert res_publish == 1

            # 3. Assert mock payload mapping
            expected_payload = RESPEncoder.encode(["message", "route_test", "SecretData!"])

            writer_d.write.assert_called_once_with(expected_payload)
            writer_d.drain.assert_awaited_once()

            # E shouldn't receive anything
            writer_e.write.assert_not_called()

        finally:
            app.pubsub.remove_pubsub_context(client_d)
            app.pubsub.remove_pubsub_context(client_e)
            app.pubsub.remove_pubsub_context("publisher")

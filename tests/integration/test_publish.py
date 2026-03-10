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
            # Setup subscriptions
            # client_a -> 'foo'
            assert execute_command(["SUBSCRIBE", "foo"], connection_id=client_a) == [
                "subscribe",
                "foo",
                1,
            ]

            # client_b -> 'bar'
            assert execute_command(["SUBSCRIBE", "bar"], connection_id=client_b) == [
                "subscribe",
                "bar",
                1,
            ]

            # client_c -> 'bar'
            assert execute_command(["SUBSCRIBE", "bar"], connection_id=client_c) == [
                "subscribe",
                "bar",
                1,
            ]

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

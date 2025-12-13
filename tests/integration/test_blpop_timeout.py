"""Integration tests for BLPOP timeout behavior."""

import asyncio
import time

from app.handler import execute_command as async_execute_command
from app.resp import RESPEncoder
from tests.helpers import execute_command


class TestBlpopTimeout:
    """Test BLPOP timeout behavior - null array when timeout expires."""

    def test_blpop_returns_none_after_timeout(self):
        """BLPOP should return None after timeout with no data."""

        async def test():
            start = time.time()
            result = await async_execute_command(["BLPOP", "nonexistent", "0.5"])
            elapsed = time.time() - start

            assert result == {"null_array": True}
            assert 0.4 < elapsed < 0.7  # Around 0.5 seconds

        asyncio.run(test())

    def test_blpop_none_encodes_to_null_array(self):
        """Null array marker should encode to RESP null array *-1\\r\\n."""
        encoded = RESPEncoder.encode({"null_array": True})
        assert encoded == b"*-1\r\n"

    def test_blpop_returns_element_before_timeout(self):
        """BLPOP should return element if pushed before timeout."""

        async def test():
            # Start BLPOP with 2 second timeout
            async def push_after_delay():
                await asyncio.sleep(0.2)
                await async_execute_command(["RPUSH", "mylist", "quick_data"])

            start = time.time()
            push_task = asyncio.create_task(push_after_delay())
            result = await async_execute_command(["BLPOP", "mylist", "2"])
            await push_task
            elapsed = time.time() - start

            # Should return before timeout
            assert result == ["mylist", "quick_data"]
            assert elapsed < 1  # Much less than 2 second timeout

        asyncio.run(test())

    def test_blpop_very_short_timeout(self):
        """BLPOP with very short timeout (0.1s) works correctly."""

        async def test():
            start = time.time()
            result = await async_execute_command(["BLPOP", "empty", "0.1"])
            elapsed = time.time() - start

            assert result == {"null_array": True}
            assert 0.05 < elapsed < 0.2

        asyncio.run(test())

    def test_blpop_timeout_vs_zero_timeout(self):
        """Compare timed timeout vs zero (infinite) timeout behavior."""

        async def test():
            # Timed timeout - returns null_array
            result1 = await async_execute_command(["BLPOP", "test1", "0.2"])
            assert result1 == {"null_array": True}

            # Zero timeout with data - returns immediately
            await async_execute_command(["RPUSH", "test2", "data"])
            result2 = await async_execute_command(["BLPOP", "test2", "0"])
            assert result2 == ["test2", "data"]

        asyncio.run(test())

    def test_blpop_timeout_with_late_push(self):
        """Element pushed after timeout shouldn't affect result."""

        async def test():
            # Push arrives AFTER timeout
            async def push_too_late():
                await asyncio.sleep(0.6)
                await async_execute_command(["RPUSH", "late_list", "too_late"])

            push_task = asyncio.create_task(push_too_late())
            result = await async_execute_command(["BLPOP", "late_list", "0.3"])

            # Should timeout
            assert result == {"null_array": True}

            # Wait for late push to complete
            await push_task

            # Element should still be in list
            remaining = await async_execute_command(["LRANGE", "late_list", "0", "-1"])
            assert remaining == ["too_late"]

        asyncio.run(test())

    def test_blpop_multiple_timeouts_different_durations(self):
        """Multiple BLPOPs with different timeouts."""

        async def test():
            # Start 3 BLPOPs with different timeouts
            blpop1 = asyncio.create_task(async_execute_command(["BLPOP", "list", "0.2"]))
            blpop2 = asyncio.create_task(async_execute_command(["BLPOP", "list", "0.5"]))
            blpop3 = asyncio.create_task(async_execute_command(["BLPOP", "list", "1.0"]))

            await asyncio.sleep(0.3)

            # First should be done (timeout)
            assert blpop1.done()
            assert await blpop1 == {"null_array": True}

            # Second and third still waiting
            assert not blpop2.done()
            assert not blpop3.done()

            # Push data - should wake one of the remaining
            await async_execute_command(["RPUSH", "list", "data"])
            await asyncio.sleep(0.1)

            # One should get the data
            results = []
            if blpop2.done():
                results.append(await blpop2)
            if blpop3.done():
                results.append(await blpop3)

            assert ["list", "data"] in results

            # Cancel any still waiting
            for task in [blpop2, blpop3]:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

        asyncio.run(test())

    def test_blpop_timeout_precision(self):
        """BLPOP timeout should be reasonably precise."""

        async def test():
            timeouts = [0.1, 0.5, 1.0]

            for timeout_val in timeouts:
                start = time.time()
                result = await async_execute_command(
                    ["BLPOP", f"key_{timeout_val}", str(timeout_val)]
                )
                elapsed = time.time() - start

                assert result == {"null_array": True}
                # Allow 30% variance for system timing
                assert timeout_val * 0.7 < elapsed < timeout_val * 1.3, (
                    f"Timeout {timeout_val}s took {elapsed:.3f}s"
                )

        asyncio.run(test())


class TestBlpopTimeoutEdgeCases:
    """Edge cases for BLPOP timeout behavior."""

    def test_blpop_fractional_timeout(self):
        """BLPOP accepts fractional timeout values."""

        async def test():
            start = time.time()
            result = await async_execute_command(["BLPOP", "test", "0.25"])
            elapsed = time.time() - start

            assert result == {"null_array": True}
            assert 0.2 < elapsed < 0.4

        asyncio.run(test())

    def test_blpop_element_exactly_at_timeout(self):
        """Element arriving right at timeout boundary."""

        async def test():
            # Push at ~0.3s, timeout at 0.35s
            async def push_at_boundary():
                await asyncio.sleep(0.28)
                await async_execute_command(["RPUSH", "boundary", "just_in_time"])

            push_task = asyncio.create_task(push_at_boundary())
            result = await async_execute_command(["BLPOP", "boundary", "0.35"])
            await push_task

            # Should get the element (just before timeout)
            assert result == ["boundary", "just_in_time"]

        asyncio.run(test())

    def test_blpop_timeout_with_existing_key_empty_list(self):
        """BLPOP on existing but empty list should timeout."""
        # Create empty list by popping all elements
        execute_command(["RPUSH", "mylist", "temp"])
        execute_command(["LPOP", "mylist", "1"])

        # List exists but is empty - should timeout
        async def test():
            start = time.time()
            result = await async_execute_command(["BLPOP", "mylist", "0.2"])
            elapsed = time.time() - start

            assert result == {"null_array": True}
            assert 0.15 < elapsed < 0.3

        asyncio.run(test())

    def test_blpop_respects_fifo_order_with_timeout(self):
        """Multiple waiters with timeouts should maintain FIFO order."""

        async def test():
            # Start 3 waiters
            waiters = [
                asyncio.create_task(async_execute_command(["BLPOP", "fifo", "2"])) for _ in range(3)
            ]

            await asyncio.sleep(0.1)

            # Push one element
            await async_execute_command(["RPUSH", "fifo", "first"])
            await asyncio.sleep(0.05)

            # First waiter should get it
            assert waiters[0].done()
            assert await waiters[0] == ["fifo", "first"]

            # Others still waiting
            assert not waiters[1].done()
            assert not waiters[2].done()

            # Cancel remaining
            for w in waiters[1:]:
                w.cancel()
                try:
                    await w
                except asyncio.CancelledError:
                    pass

        asyncio.run(test())

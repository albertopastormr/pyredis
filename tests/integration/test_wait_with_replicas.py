"""Integration tests for WAIT command with replicas."""

import asyncio

import pytest

from app.commands.wait import WaitCommand
from app.replica_manager import ReplicaManager


class MockReader:
    """Mock stream reader for testing."""

    def __init__(self):
        self.data_queue = asyncio.Queue()

    async def read(self, n: int) -> bytes:
        """Read data from queue."""
        return await self.data_queue.get()

    def feed_data(self, data: bytes):
        """Feed data to be read."""
        self.data_queue.put_nowait(data)


class MockWriter:
    """Mock stream writer for testing."""

    def __init__(self):
        self.written_data = []

    def write(self, data: bytes):
        self.written_data.append(data)

    async def drain(self):
        pass


@pytest.mark.asyncio
class TestWaitWithReplicas:
    """Test WAIT command with connected replicas."""

    async def test_wait_with_no_replicas(self):
        """WAIT returns 0 when no replicas are connected."""
        # Reset replica manager
        ReplicaManager.reset()

        cmd = WaitCommand()
        result = await cmd.execute(["3", "1000"])

        assert result == 0

    async def test_wait_with_replicas_connected(self):
        """WAIT returns the number of connected replicas."""
        # Reset and add replicas
        ReplicaManager.reset()

        # Simulate 3 connected replicas
        ReplicaManager.add_replica("replica1", MockReader(), MockWriter())
        ReplicaManager.add_replica("replica2", MockReader(), MockWriter())
        ReplicaManager.add_replica("replica3", MockReader(), MockWriter())

        cmd = WaitCommand()

        # When offset is 0, returns all connected replicas
        result = await cmd.execute(["2", "1000"])
        assert result == 3

        # Asking for 5, returns 3 (only 3 connected)
        result = await cmd.execute(["5", "1000"])
        assert result == 3

        # Asking for 0, returns 3
        result = await cmd.execute(["0", "1000"])
        assert result == 3

        # Clean up
        ReplicaManager.reset()

    async def test_wait_with_seven_replicas(self):
        """WAIT returns 7 when 7 replicas are connected (matches example)."""
        # Reset and add 7 replicas
        ReplicaManager.reset()

        for i in range(7):
            ReplicaManager.add_replica(f"replica{i}", MockReader(), MockWriter())

        cmd = WaitCommand()

        # All scenarios from the example should return 7 (when offset is 0)
        result = await cmd.execute(["3", "500"])
        assert result == 7

        result = await cmd.execute(["7", "500"])
        assert result == 7

        result = await cmd.execute(["9", "500"])
        assert result == 7

        # Clean up
        ReplicaManager.reset()

    async def test_wait_ignores_numreplicas_argument(self):
        """WAIT ignores numreplicas and just returns connected count (when offset is 0)."""
        ReplicaManager.reset()

        # Add 5 replicas
        for i in range(5):
            ReplicaManager.add_replica(f"replica{i}", MockReader(), MockWriter())

        cmd = WaitCommand()

        # Different numreplicas values all return 5 (when offset is 0)
        assert await cmd.execute(["1", "1000"]) == 5
        assert await cmd.execute(["10", "1000"]) == 5
        assert await cmd.execute(["0", "1000"]) == 5

        # Clean up
        ReplicaManager.reset()

    async def test_wait_waits_for_acks(self):
        """WAIT blocks until ACKs are received when offset > 0."""
        ReplicaManager.reset()
        ReplicaManager.add_replica("replica1", MockReader(), MockWriter())
        ReplicaManager.add_replica("replica2", MockReader(), MockWriter())

        # Simulate some writes (increases master offset)
        await ReplicaManager.propagate_command("SET", ["foo", "bar"])
        current_offset = ReplicaManager.get_master_offset()
        assert current_offset > 0

        cmd = WaitCommand()

        # Start WAIT in a background task (wait for 2 replicas)
        wait_task = asyncio.create_task(cmd.execute(["2", "2000"]))

        # Give it a moment to send GETACKs and start waiting
        await asyncio.sleep(0.1)

        # Verify it hasn't completed yet
        assert not wait_task.done()

        # ACK from first replica
        await ReplicaManager.update_replica_ack("replica1", current_offset)

        # Should still be waiting (need 2)
        await asyncio.sleep(0.01)
        assert not wait_task.done()

        # ACK from second replica
        await ReplicaManager.update_replica_ack("replica2", current_offset)

        # Should complete now
        result = await asyncio.wait_for(wait_task, timeout=0.1)
        assert result == 2

        ReplicaManager.reset()

    async def test_wait_timeout(self):
        """WAIT returns currently acknowledged count after timeout."""
        ReplicaManager.reset()
        ReplicaManager.add_replica("replica1", MockReader(), MockWriter())
        ReplicaManager.add_replica("replica2", MockReader(), MockWriter())

        # Simulate some writes
        await ReplicaManager.propagate_command("SET", ["foo", "bar"])
        current_offset = ReplicaManager.get_master_offset()

        cmd = WaitCommand()

        # Start WAIT in a background task (wait for 2 replicas, timeout 200ms)
        wait_task = asyncio.create_task(cmd.execute(["2", "200"]))

        # ACK only one replica
        await ReplicaManager.update_replica_ack("replica1", current_offset)

        # Wait for timeout
        result = await wait_task

        # Should return 1 (only 1 acknowledged)
        assert result == 1

        ReplicaManager.reset()

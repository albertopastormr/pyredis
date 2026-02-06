"""Integration tests for WAIT command with replicas."""

import asyncio

from app.commands.wait import WaitCommand
from app.replica_manager import ReplicaManager


class MockWriter:
    """Mock stream writer for testing."""
    
    def __init__(self):
        self.written_data = []
    
    def write(self, data: bytes):
        self.written_data.append(data)
    
    async def drain(self):
        pass


class TestWaitWithReplicas:
    """Test WAIT command with connected replicas."""

    def test_wait_with_no_replicas(self):
        """WAIT returns 0 when no replicas are connected."""
        # Reset replica manager
        ReplicaManager.reset()
        
        cmd = WaitCommand()
        result = asyncio.run(cmd.execute(["3", "1000"]))
        
        assert result == 0

    def test_wait_with_replicas_connected(self):
        """WAIT returns the number of connected replicas."""
        # Reset and add replicas
        ReplicaManager.reset()
        
        # Simulate 3 connected replicas
        ReplicaManager.add_replica("replica1", MockWriter())
        ReplicaManager.add_replica("replica2", MockWriter())
        ReplicaManager.add_replica("replica3", MockWriter())
        
        cmd = WaitCommand()
        
        # Asking for 2, returns 3 (all connected)
        result = asyncio.run(cmd.execute(["2", "1000"]))
        assert result == 3
        
        # Asking for 5, returns 3 (only 3 connected)
        result = asyncio.run(cmd.execute(["5", "1000"]))
        assert result == 3
        
        # Asking for 0, returns 3
        result = asyncio.run(cmd.execute(["0", "1000"]))
        assert result == 3
        
        # Clean up
        ReplicaManager.reset()

    def test_wait_with_seven_replicas(self):
        """WAIT returns 7 when 7 replicas are connected (matches example)."""
        # Reset and add 7 replicas
        ReplicaManager.reset()
        
        for i in range(7):
            ReplicaManager.add_replica(f"replica{i}", MockWriter())
        
        cmd = WaitCommand()
        
        # All scenarios from the example should return 7
        result = asyncio.run(cmd.execute(["3", "500"]))
        assert result == 7
        
        result = asyncio.run(cmd.execute(["7", "500"]))
        assert result == 7
        
        result = asyncio.run(cmd.execute(["9", "500"]))
        assert result == 7
        
        # Clean up
        ReplicaManager.reset()

    def test_wait_ignores_numreplicas_argument(self):
        """WAIT ignores numreplicas and just returns connected count."""
        ReplicaManager.reset()
        
        # Add 5 replicas
        for i in range(5):
            ReplicaManager.add_replica(f"replica{i}", MockWriter())
        
        cmd = WaitCommand()
        
        # Different numreplicas values all return 5
        assert asyncio.run(cmd.execute(["1", "1000"])) == 5
        assert asyncio.run(cmd.execute(["10", "1000"])) == 5
        assert asyncio.run(cmd.execute(["0", "1000"])) == 5
        
        # Clean up
        ReplicaManager.reset()

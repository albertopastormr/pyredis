"""Unit tests for WAIT command."""

import asyncio
import pytest

from app.commands.wait import WaitCommand
from app.replica_manager import ReplicaManager


class TestWaitCommand:
    """Test WAIT command."""

    def test_name(self):
        """Command name is WAIT."""
        cmd = WaitCommand()
        assert cmd.name == "WAIT"

    def test_wait_with_zero_replicas(self):
        """WAIT 0 <timeout> should return replica count (0 if none connected)."""
        ReplicaManager.reset()

        cmd = WaitCommand()
        result = asyncio.run(cmd.execute(["0", "1000"]))

        # Returns 0 because no replicas are connected
        assert result == 0

    def test_wait_requires_two_args(self):
        """WAIT requires exactly 2 arguments."""
        cmd = WaitCommand()

        # Too few arguments
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(cmd.execute(["0"]))

        # Too many arguments
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(cmd.execute(["0", "1000", "extra"]))

    def test_wait_requires_integer_args(self):
        """WAIT arguments must be integers."""
        cmd = WaitCommand()

        # Non-integer numreplicas
        with pytest.raises(ValueError, match="value is not an integer"):
            asyncio.run(cmd.execute(["abc", "1000"]))

        # Non-integer timeout
        with pytest.raises(ValueError, match="value is not an integer"):
            asyncio.run(cmd.execute(["0", "xyz"]))

    def test_wait_rejects_negative_numreplicas(self):
        """WAIT rejects negative numreplicas."""
        cmd = WaitCommand()

        with pytest.raises(ValueError, match="numreplicas must be non-negative"):
            asyncio.run(cmd.execute(["-1", "1000"]))

    def test_wait_rejects_negative_timeout(self):
        """WAIT rejects negative timeout."""
        cmd = WaitCommand()

        with pytest.raises(ValueError, match="timeout must be non-negative"):
            asyncio.run(cmd.execute(["0", "-1"]))

    def test_wait_with_positive_replicas_no_replicas_connected(self):
        """WAIT with positive numreplicas returns 0 when no replicas are connected."""
        ReplicaManager.reset()

        cmd = WaitCommand()

        # Returns 0 because no replicas are connected
        result = asyncio.run(cmd.execute(["3", "5000"]))
        assert result == 0

    def test_wait_accepts_zero_timeout(self):
        """WAIT accepts 0 as timeout (no wait)."""
        ReplicaManager.reset()

        cmd = WaitCommand()

        result = asyncio.run(cmd.execute(["0", "0"]))
        assert result == 0

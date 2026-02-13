"""WAIT command implementation."""

from typing import Any

from .base import BaseCommand


class WaitCommand(BaseCommand):
    """
    WAIT command - Wait for a number of replicas to acknowledge write commands.

    Syntax: WAIT <numreplicas> <timeout>

    Arguments:
        numreplicas: Minimum number of replicas that must acknowledge
        timeout: Maximum time in milliseconds to wait

    Returns:
        Integer - Number of replicas that acknowledged
    """

    @property
    def name(self) -> str:
        return "WAIT"

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute WAIT command.

        Args:
            args: [numreplicas, timeout]

        Returns:
            Integer - Number of replicas that acknowledged
        """
        self.validate_args(args, min_args=2, max_args=2)

        try:
            numreplicas = int(args[0])
            timeout = int(args[1])
        except ValueError:
            raise ValueError("ERR value is not an integer or out of range")

        if numreplicas < 0:
            raise ValueError("ERR numreplicas must be non-negative")

        if timeout < 0:
            raise ValueError("ERR timeout must be non-negative")

        from ..replica_manager import ReplicaManager

        acknowledged_count = await ReplicaManager.wait_for_replication(numreplicas, timeout)

        return acknowledged_count

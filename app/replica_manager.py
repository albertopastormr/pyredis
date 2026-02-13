"""Replica connection management and command propagation."""

import asyncio
import logging
from typing import Any

from .resp import RESPEncoder

logger = logging.getLogger(__name__)


class ReplicaManager:
    """
    Manages connected replicas and handles command propagation.

    Static class that maintains a registry of all connected replicas
    and propagates write commands to them.
    """

    _replicas: dict[Any, tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}
    _master_offset: int = 0
    _replica_offsets: dict[Any, int] = {}
    _ack_condition: asyncio.Condition | None = None

    @classmethod
    def _get_condition(cls) -> asyncio.Condition:
        """Get or create the condition variable bound to current loop."""
        if cls._ack_condition is None:
            cls._ack_condition = asyncio.Condition()
        return cls._ack_condition

    @classmethod
    def add_replica(
        cls, connection_id: Any, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """
        Register a new replica connection after handshake completion.

        Args:
            connection_id: Unique identifier for the connection
            reader: Async stream reader for receiving data from replica
            writer: Async stream writer for sending data to replica
        """
        cls._replicas[connection_id] = (reader, writer)
        cls._replica_offsets[connection_id] = 0
        logger.info(
            f"[ReplicaManager] Added replica: {connection_id}. Total replicas: {len(cls._replicas)}"
        )

    @classmethod
    def remove_replica(cls, connection_id: Any) -> None:
        """
        Remove a replica connection when it disconnects.

        Args:
            connection_id: Connection identifier to remove
        """
        if connection_id in cls._replicas:
            del cls._replicas[connection_id]
        if connection_id in cls._replica_offsets:
            del cls._replica_offsets[connection_id]
            logger.info(
                f"[ReplicaManager] Removed replica: {connection_id}. Total replicas: {len(cls._replicas)}"
            )

    @classmethod
    async def propagate_command(cls, command_name: str, args: list[str]) -> None:
        """
        Propagate a write command to all connected replicas.

        Encodes the command as a RESP array and sends it to all replicas
        over their replication connections. Does not wait for responses.

        Args:
            command_name: Name of the command (e.g., "SET", "DEL")
            args: Command arguments
        """
        if not cls._replicas:
            return

        command_array = [command_name.upper(), *args]
        encoded = RESPEncoder.encode(command_array)

        logger.info(
            f"[ReplicaManager] Propagating {command_name} to {len(cls._replicas)} replica(s)"
        )

        # Send to all replicas without waiting for response
        for connection_id, (_reader, writer) in cls._replicas.items():
            try:
                writer.write(encoded)
                await writer.drain()
            except Exception as e:
                logger.error(f"[ReplicaManager] Error propagating to {connection_id}: {e}")

        # Update master offset
        cls._master_offset += len(encoded)
        logger.debug(f"[ReplicaManager] Master offset now: {cls._master_offset}")

    @classmethod
    async def update_replica_ack(cls, connection_id: Any, offset: int) -> None:
        """
        Update the acknowledged offset for a replica.

        Args:
            connection_id: Replica connection ID
            offset: The offset acknowledged by the replica
        """
        if connection_id in cls._replicas:
            cls._replica_offsets[connection_id] = offset
            logger.debug(f"[ReplicaManager] Replica {connection_id} acked offset {offset}")

            condition = cls._get_condition()
            async with condition:
                condition.notify_all()

    @classmethod
    async def wait_for_replication(cls, numreplicas: int, timeout_ms: int) -> int:
        """
        Wait for replicas to acknowledge replication up to current offset.

        Args:
            numreplicas: Minimum number of replicas to wait for
            timeout_ms: Maximum time to wait in milliseconds

        Returns:
            Number of replicas that acknowledged
        """
        if not cls._replicas:
            return 0

        target_offset = cls._master_offset
        logger.debug(
            f"[ReplicaManager] Waiting for {numreplicas} replicas to reach offset {target_offset}"
        )

        if target_offset == 0:
            return len(cls._replicas)

        # Send GETACK to all replicas
        getack_command = RESPEncoder.encode(["REPLCONF", "GETACK", "*"])
        for connection_id, (_reader, writer) in cls._replicas.items():
            try:
                writer.write(getack_command)
                await writer.drain()
            except Exception as e:
                logger.error(f"[ReplicaManager] Error sending GETACK to {connection_id}: {e}")

        # Wait for ACKs
        condition = cls._get_condition()

        async def _wait_condition():
            async with condition:
                await condition.wait_for(lambda: cls._count_acks(target_offset) >= numreplicas)
                return cls._count_acks(target_offset)

        try:
            return await asyncio.wait_for(_wait_condition(), timeout=timeout_ms / 1000.0)
        except asyncio.TimeoutError:
            logger.warning("[ReplicaManager] Timeout waiting for ACKs")
            return cls._count_acks(target_offset)

    @classmethod
    def _count_acks(cls, target_offset: int) -> int:
        """Count replicas that have reached the target offset."""
        count = 0
        for offset in cls._replica_offsets.values():
            if offset >= target_offset:
                count += 1
        return count

    @classmethod
    def get_replica_count(cls) -> int:
        """Get the number of connected replicas."""
        return len(cls._replicas)

    @classmethod
    def get_master_offset(cls) -> int:
        """Get the current master replication offset."""
        return cls._master_offset

    @classmethod
    def reset(cls) -> None:
        """Reset the replica registry (for testing)."""
        cls._replicas.clear()
        cls._master_offset = 0
        cls._replica_offsets.clear()
        cls._ack_condition = None  # Force recreation on new loop

"""Replica connection management and command propagation."""

import asyncio
from typing import Any

from .resp import RESPEncoder


class ReplicaManager:
    """
    Manages connected replicas and handles command propagation.
    
    Static class that maintains a registry of all connected replicas
    and propagates write commands to them.
    """

    _replicas: dict[Any, asyncio.StreamWriter] = {}

    @classmethod
    def add_replica(cls, connection_id: Any, writer: asyncio.StreamWriter) -> None:
        """
        Register a new replica connection after handshake completion.

        Args:
            connection_id: Unique identifier for the connection
            writer: Async stream writer for sending data to replica
        """
        cls._replicas[connection_id] = writer
        print(f"[ReplicaManager] Added replica: {connection_id}. Total replicas: {len(cls._replicas)}")

    @classmethod
    def remove_replica(cls, connection_id: Any) -> None:
        """
        Remove a replica connection when it disconnects.

        Args:
            connection_id: Connection identifier to remove
        """
        if connection_id in cls._replicas:
            del cls._replicas[connection_id]
            print(f"[ReplicaManager] Removed replica: {connection_id}. Total replicas: {len(cls._replicas)}")

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

        print(f"[ReplicaManager] Propagating {command_name} to {len(cls._replicas)} replica(s)")

        # Send to all replicas without waiting for response
        for connection_id, writer in cls._replicas.items():
            try:
                writer.write(encoded)
                await writer.drain()
            except Exception as e:
                print(f"[ReplicaManager] Error propagating to {connection_id}: {e}")

    @classmethod
    def get_replica_count(cls) -> int:
        """Get the number of connected replicas."""
        return len(cls._replicas)

    @classmethod
    def reset(cls) -> None:
        """Reset the replica registry (for testing)."""
        cls._replicas.clear()

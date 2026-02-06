"""Replica connection management and command propagation."""

import asyncio
from typing import Any

from .resp import RESPEncoder, RESPParser


class ReplicaManager:
    """
    Manages connected replicas and handles command propagation.
    
    Static class that maintains a registry of all connected replicas
    and propagates write commands to them.
    """

    _replicas: dict[Any, tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}
    _master_offset: int = 0  # Track bytes propagated to replicas

    @classmethod
    def add_replica(cls, connection_id: Any, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """
        Register a new replica connection after handshake completion.

        Args:
            connection_id: Unique identifier for the connection
            reader: Async stream reader for receiving data from replica
            writer: Async stream writer for sending data to replica
        """
        cls._replicas[connection_id] = (reader, writer)
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
        for connection_id, (reader, writer) in cls._replicas.items():
            try:
                writer.write(encoded)
                await writer.drain()
            except Exception as e:
                print(f"[ReplicaManager] Error propagating to {connection_id}: {e}")
        
        # Update master offset
        cls._master_offset += len(encoded)
        print(f"[ReplicaManager] Master offset now: {cls._master_offset}")

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
        print(f"[ReplicaManager] Waiting for {numreplicas} replicas to reach offset {target_offset}")
        
        # If no write commands have been sent (offset is 0), all replicas are in sync
        if target_offset == 0:
            return len(cls._replicas)
        
        getack_command = RESPEncoder.encode(["REPLCONF", "GETACK", "*"])
        
        for connection_id, (reader, writer) in cls._replicas.items():
            try:
                writer.write(getack_command)
                await writer.drain()
                print(f"[ReplicaManager] Sent GETACK to {connection_id}")
            except Exception as e:
                print(f"[ReplicaManager] Error sending GETACK to {connection_id}: {e}")
        
        # Wait for ACK responses with timeout
        acknowledged_count = 0
        timeout_seconds = timeout_ms / 1000.0
        
        try:
            acknowledged_count = await asyncio.wait_for(
                cls._collect_acks(target_offset, numreplicas),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            print(f"[ReplicaManager] Timeout waiting for ACKs")
            # Count how many replicas acknowledged before timeout
            acknowledged_count = await cls._count_current_acks(target_offset)
        
        print(f"[ReplicaManager] {acknowledged_count} replicas acknowledged offset {target_offset}")
        return acknowledged_count
    
    @classmethod
    async def _collect_acks(cls, target_offset: int, required_count: int) -> int:
        """
        Collect ACK responses from replicas.
        
        Args:
            target_offset: The offset to check for
            required_count: Return as soon as this many replicas acknowledge
            
        Returns:
            Number of replicas that acknowledged
        """
        acknowledged = set()
        
        # Create tasks to read from all replicas
        tasks = []
        for connection_id, (reader, writer) in cls._replicas.items():
            tasks.append(cls._read_ack(connection_id, reader, target_offset))
        
        # Wait for responses
        for task in asyncio.as_completed(tasks):
            try:
                connection_id, ack_offset = await task
                if ack_offset >= target_offset:
                    acknowledged.add(connection_id)
                    print(f"[ReplicaManager] Replica {connection_id} acknowledged offset {ack_offset}")
                    
                    # Return early if we have enough
                    if len(acknowledged) >= required_count:
                        return len(acknowledged)
            except Exception as e:
                print(f"[ReplicaManager] Error reading ACK: {e}")
        
        return len(acknowledged)
    
    @classmethod
    async def _read_ack(cls, connection_id: Any, reader: asyncio.StreamReader, target_offset: int) -> tuple[Any, int]:
        """
        Read ACK response from a single replica.
        
        Args:
            connection_id: Replica connection ID
            reader: Stream reader for the replica
            target_offset: Expected offset
            
        Returns:
            Tuple of (connection_id, ack_offset)
        """
        try:
            data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
            if not data:
                raise ValueError("No data received")
            
            response = RESPParser.parse(data)
            if isinstance(response, list) and len(response) == 3:
                if response[0].upper() == "REPLCONF" and response[1].upper() == "ACK":
                    ack_offset = int(response[2])
                    return (connection_id, ack_offset)
            
            raise ValueError(f"Invalid ACK response: {response}")
        except Exception as e:
            print(f"[ReplicaManager] Error reading ACK from {connection_id}: {e}")
            return (connection_id, -1)
    
    @classmethod
    async def _count_current_acks(cls, target_offset: int) -> int:
        """
        Count how many replicas have already acknowledged (used after timeout).
        
        Args:
            target_offset: The offset to check for
            
        Returns:
            Number of replicas at or past the target offset
        """
        # This is a simplified version - we'd track the last known offset
        return 0

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

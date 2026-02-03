"""Replication - handles replica-to-master connection and handshaking."""

import asyncio
import logging
from typing import Optional

from .config import ServerConfig
from .resp import RESPEncoder

logger = logging.getLogger(__name__)


class ReplicationClient:
    """Handles replication client operations for a replica server."""

    def __init__(self, master_host: str, master_port: int):
        """
        Initialize replication client.

        Args:
            master_host: Master server hostname
            master_port: Master server port
        """
        self.master_host = master_host
        self.master_port = master_port
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def connect(self) -> None:
        """
        Connect to the master server.

        Raises:
            ConnectionError: If connection fails
        """
        try:
            logger.info(f"Connecting to master at {self.master_host}:{self.master_port}")
            self.reader, self.writer = await asyncio.open_connection(
                self.master_host, self.master_port
            )
            logger.info("✅ Connected to master server")
        except Exception as e:
            logger.error(f"❌ Failed to connect to master: {e}")
            raise ConnectionError(f"Failed to connect to master: {e}")

    async def send_ping(self) -> None:
        """
        Send PING command to master as first step of handshake.

        The PING command is sent as a RESP array
        """
        if not self.writer:
            raise RuntimeError("Not connected to master")

        ping_command = RESPEncoder.encode(["PING"])
        
        logger.info("Sending PING to master...")
        self.writer.write(ping_command)
        await self.writer.drain()
        logger.info("✅ PING sent to master")

    async def start_handshake(self) -> None:
        """
        Perform the complete handshake with the master.

        For now, this only sends PING. Future steps will include REPLCONF and PSYNC.
        """
        await self.connect()
        await self.send_ping()
        # TODO: Add REPLCONF and PSYNC in later stages

    async def close(self) -> None:
        """Close the connection to master."""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()


async def connect_to_master() -> None:
    """
    Initiate connection to master server when running as replica.

    Reads master host and port from ServerConfig and performs handshake.
    """
    repl_config = ServerConfig.get_replication_config()
    
    if not repl_config.is_slave():
        logger.warning("Not running as replica, skipping master connection")
        return

    if not repl_config.master_host or not repl_config.master_port:
        logger.error("Master host/port not configured")
        return

    client = ReplicationClient(
        master_host=repl_config.master_host,
        master_port=repl_config.master_port,
    )

    try:
        await client.start_handshake()
    except Exception as e:
        logger.error(f"Handshake failed: {e}")
        # Don't crash the server, just log the error

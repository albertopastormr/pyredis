"""Replication - handles replica-to-master connection and handshaking."""

import asyncio
import logging
from typing import Optional

from .config import ServerConfig
from .resp import RESPEncoder, RESPParser

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

    async def send_replconf_listening_port(self, port: int) -> None:
        """
        Send REPLCONF listening-port command to master.
        
        Args:
            port: The port this replica is listening on
            
        The command is sent as: REPLCONF listening-port <PORT>
        """
        if not self.writer:
            raise RuntimeError("Not connected to master")

        replconf_command = RESPEncoder.encode(["REPLCONF", "listening-port", str(port)])
        
        logger.info(f"Sending REPLCONF listening-port {port} to master...")
        self.writer.write(replconf_command)
        await self.writer.drain()
        
        # Read and parse response (expecting +OK\r\n)
        response_data = await self.reader.read(1024)
        response = RESPParser.parse(response_data)
        if response != "OK":
            raise RuntimeError(f"Unexpected response to REPLCONF listening-port: {response}")
        
        logger.info("✅ REPLCONF listening-port acknowledged")

    async def send_replconf_capa(self) -> None:
        """
        Send REPLCONF capa psync2 command to master.
        
        This notifies the master that the replica supports PSYNC2 protocol.
        """
        if not self.writer:
            raise RuntimeError("Not connected to master")

        replconf_command = RESPEncoder.encode(["REPLCONF", "capa", "psync2"])
        
        logger.info("Sending REPLCONF capa psync2 to master...")
        self.writer.write(replconf_command)
        await self.writer.drain()
        
        # Read and parse response (expecting +OK\r\n)
        response_data = await self.reader.read(1024)
        response = RESPParser.parse(response_data)
        if response != "OK":
            raise RuntimeError(f"Unexpected response to REPLCONF capa: {response}")
        
        logger.info("✅ REPLCONF capa acknowledged")


    async def start_handshake(self) -> None:
        """
        Perform the complete handshake with the master.

        Sequence:
        1. PING - Test connection
        2. REPLCONF listening-port - Tell master our listening port
        3. REPLCONF capa psync2 - Tell master our capabilities
        """
        await self.connect()
        await self.send_ping()
        
        listening_port = ServerConfig.get_listening_port()
        await self.send_replconf_listening_port(listening_port)
        await self.send_replconf_capa()
        
        logger.info("✅ Handshake complete")

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

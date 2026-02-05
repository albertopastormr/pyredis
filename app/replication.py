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

        The PING command is sent as a RESP array and expects a +PONG response.
        """
        if not self.writer:
            raise RuntimeError("Not connected to master")

        ping_command = RESPEncoder.encode(["PING"])
        
        logger.info("Sending PING to master...")
        self.writer.write(ping_command)
        await self.writer.drain()
        
        # Read and parse response (expecting +PONG\r\n)
        response_line = await self.reader.readuntil(b'\r\n')
        response = response_line.decode('utf-8').strip()
        
        if response != "+PONG":
            raise RuntimeError(f"Unexpected response to PING: {response}")
        
        logger.info("✅ PING acknowledged with PONG")

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
        
        response_line = await self.reader.readuntil(b'\r\n')
        response = response_line.decode('utf-8').strip()
        if response != "+OK":
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
        
        response_line = await self.reader.readuntil(b'\r\n')
        response = response_line.decode('utf-8').strip()
        if response != "+OK":
            raise RuntimeError(f"Unexpected response to REPLCONF capa: {response}")
        
        logger.info("✅ REPLCONF capa acknowledged")

    async def send_psync(self, repl_id: str = "?", offset: int = -1) -> None:
        """
        Send PSYNC command to master to initiate synchronization.
        
        Args:
            repl_id: Replication ID (use "?" for initial sync)
            offset: Replication offset (use -1 for initial sync)
            
        The command is sent as: PSYNC <repl_id> <offset>
        For initial sync: PSYNC ? -1
        
        The master responds with: +FULLRESYNC <REPL_ID> 0\r\n
        """
        if not self.writer:
            raise RuntimeError("Not connected to master")

        psync_command = RESPEncoder.encode(["PSYNC", repl_id, str(offset)])
        
        logger.info(f"Sending PSYNC {repl_id} {offset} to master...")
        self.writer.write(psync_command)
        await self.writer.drain()
        
        # Read only the FULLRESYNC line (not bulk read that might consume RDB)
        response_line = await self.reader.readuntil(b'\r\n')
        response = response_line.decode('utf-8').strip()
        
        if not response.startswith("+FULLRESYNC"):
            raise RuntimeError(f"Unexpected response to PSYNC: {response}")
        
        # Parse: +FULLRESYNC <repl_id> <offset>
        parts = response[1:].split()  # Skip the '+'
        if len(parts) == 3:
            master_repl_id = parts[1]
            master_offset = parts[2]
            logger.info(f"✅ PSYNC acknowledged: FULLRESYNC {master_repl_id} {master_offset}")
        else:
            logger.info(f"✅ PSYNC acknowledged: {response}")
    
    async def receive_rdb_file(self) -> None:
        """
        Receive the RDB file from master after PSYNC.
        
        Master sends: $<length>\r\n<binary_data>
        For empty RDB, it's $88\r\n followed by 88 bytes
        """
        if not self.reader:
            raise RuntimeError("Not connected to master")
        
        logger.info("Waiting for RDB file from master...")
        
        # Read the bulk string header: $<length>\r\n
        header_data = await self.reader.readuntil(b'\r\n')
        header = header_data.decode('utf-8').strip()
        
        if not header.startswith('$'):
            raise RuntimeError(f"Expected RDB bulk string, got: {header}")
        
        rdb_length = int(header[1:])
        logger.info(f"Receiving RDB file ({rdb_length} bytes)...")
        
        # Read the exact number of bytes for RDB file
        rdb_data = await self.reader.readexactly(rdb_length)
        logger.info(f"✅ Received RDB file ({len(rdb_data)} bytes)")
    
    async def process_commands(self) -> None:
        """
        Process propagated commands from master.
        
        After handshake and RDB file, master sends write commands
        that need to be executed without sending responses.
        """
        if not self.reader:
            raise RuntimeError("Not connected to master")
        
        # to avoid circular dependency
        from .handler import execute_command
        
        logger.info("📡 Ready to receive propagated commands from master")
        
        buffer = b""  # Buffer for incomplete commands
        
        while True:
            try:
                # Read data from master (may contain multiple commands)
                data = await self.reader.read(4096)
                
                if not data:
                    logger.warning("Master connection closed")
                    break
                
                # Add to buffer
                buffer += data
                
                # Parse all complete commands from buffer
                offset = 0
                while offset < len(buffer):
                    try:
                        command, new_offset = RESPParser._parse_value(buffer, offset)
                        logger.info(f"Received propagated command: {command}")
                        
                        # Execute command
                        await execute_command(command, from_replication=True)
                        
                        offset = new_offset
                    except ValueError:
                        # Incomplete command, break and wait for more data
                        break
                
                # Remove processed data from buffer
                buffer = buffer[offset:]
                    
            except Exception as e:
                logger.error(f"Error reading from master: {e}")
                break


    async def start_handshake(self) -> None:
        """
        Perform the complete handshake with the master.

        Sequence:
        1. PING - Test connection
        2. REPLCONF listening-port - Tell master our listening port
        3. REPLCONF capa psync2 - Tell master our capabilities
        4. PSYNC - Initiate synchronization
        """
        await self.connect()
        await self.send_ping()
        
        listening_port = ServerConfig.get_listening_port()
        await self.send_replconf_listening_port(listening_port)
        await self.send_replconf_capa()
        await self.send_psync()
        
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
        
        await client.receive_rdb_file()
        
        await client.process_commands()
        
    except Exception as e:
        logger.error(f"Replication failed: {e}")
        # Don't crash the server, just log the error

"""Integration tests for replication handshake."""

import asyncio

import pytest

from app.replication import ReplicationClient
from app.resp import RESPEncoder


@pytest.fixture(autouse=True)
def reset_config():
    """Reset server config before each test."""
    from app.config import ServerConfig
    
    ServerConfig.reset()
    yield
    ServerConfig.reset()


class TestReplicationIntegration:
    """Integration tests for replica handshake."""

    def test_ping_encoding_matches_resp_spec(self):
        """Verify PING command is encoded correctly in RESP format."""
        # This is what RESPEncoder should produce for PING
        ping_encoded = RESPEncoder.encode(["PING"])
        
        # Verify exact RESP format: *1\r\n$4\r\nPING\r\n
        assert ping_encoded == b"*1\r\n$4\r\nPING\r\n"
        
        # Break down the format
        assert ping_encoded.startswith(b"*1\r\n")  # Array with 1 element
        assert b"$4\r\nPING\r\n" in ping_encoded     # Bulk string of 4 bytes

    def test_replication_client_initialization(self):
        """ReplicationClient properly initializes with host and port."""
        client = ReplicationClient("localhost", 6379)
        
        assert client.master_host == "localhost"
        assert client.master_port == 6379
        assert client.reader is None
        assert client.writer is None

    def test_connection_fails_gracefully_when_server_unreachable(self):
        """Connection attempt to unreachable server raises ConnectionError."""
        client = ReplicationClient("localhost", 59999)
        
        async def attempt_connection():
            await client.connect()
        
        with pytest.raises(ConnectionError, match="Failed to connect to master"):
            asyncio.run(attempt_connection())

    def test_send_ping_requires_active_connection(self):
        """Calling send_ping without connection raises RuntimeError."""
        client = ReplicationClient("localhost", 6379)
        
        async def attempt_send():
            await client.send_ping()
        
        with pytest.raises(RuntimeError, match="Not connected to master"):
            asyncio.run(attempt_send())



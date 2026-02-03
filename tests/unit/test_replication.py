"""Unit tests for replication module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Role, ServerConfig
from app.replication import ReplicationClient, connect_to_master


@pytest.fixture
def replication_client():
    """Fixture providing a ReplicationClient instance."""
    return ReplicationClient(master_host="localhost", master_port=6379)


class TestReplicationClient:
    """Test ReplicationClient class."""

    def test_initialization(self, replication_client):
        """ReplicationClient initializes with correct parameters."""
        assert replication_client.master_host == "localhost"
        assert replication_client.master_port == 6379
        assert replication_client.reader is None
        assert replication_client.writer is None

    @patch("asyncio.open_connection")
    def test_connect_success(self, mock_open_connection, replication_client):
        """ReplicationClient successfully connects to master."""
        # Mock the connection
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        asyncio.run(replication_client.connect())

        mock_open_connection.assert_called_once_with("localhost", 6379)
        assert replication_client.reader == mock_reader
        assert replication_client.writer == mock_writer

    @patch("asyncio.open_connection")
    def test_connect_failure(self, mock_open_connection, replication_client):
        """ReplicationClient handles connection failure."""
        mock_open_connection.side_effect = ConnectionRefusedError("Connection refused")

        with pytest.raises(ConnectionError, match="Failed to connect to master"):
            asyncio.run(replication_client.connect())

    def test_send_ping_not_connected(self, replication_client):
        """send_ping raises error when not connected."""
        with pytest.raises(RuntimeError, match="Not connected to master"):
            asyncio.run(replication_client.send_ping())

    @patch("asyncio.open_connection")
    def test_send_ping_success(self, mock_open_connection, replication_client):
        """send_ping correctly sends PING command in RESP format."""
        # Mock the connection
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        asyncio.run(replication_client.connect())
        asyncio.run(replication_client.send_ping())

        # Verify PING was written
        mock_writer.write.assert_called_once()
        written_data = mock_writer.write.call_args[0][0]
        
        # Verify RESP format: *1\r\n$4\r\nPING\r\n
        assert written_data == b"*1\r\n$4\r\nPING\r\n"
        mock_writer.drain.assert_called_once()

    @patch("asyncio.open_connection")
    def test_start_handshake(self, mock_open_connection, replication_client):
        """start_handshake connects and sends PING."""
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        asyncio.run(replication_client.start_handshake())

        # Verify connection was made
        mock_open_connection.assert_called_once_with("localhost", 6379)
        
        # Verify PING was sent
        mock_writer.write.assert_called_once()
        written_data = mock_writer.write.call_args[0][0]
        assert written_data == b"*1\r\n$4\r\nPING\r\n"


class TestConnectToMaster:
    """Test connect_to_master function."""

    @patch("app.replication.ReplicationClient")
    def test_connect_to_master_as_slave(self, mock_client_class):
        """connect_to_master initiates handshake when running as slave."""
        # Configure as slave
        ServerConfig.reset()
        ServerConfig.initialize(
            role=Role.SLAVE,
            master_host="localhost",
            master_port=6379,
        )

        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        asyncio.run(connect_to_master())

        # Verify client was created with correct parameters
        mock_client_class.assert_called_once_with(
            master_host="localhost",
            master_port=6379,
        )
        
        # Verify handshake was started
        mock_client.start_handshake.assert_called_once()

    @patch("app.replication.ReplicationClient")
    def test_connect_to_master_as_master(self, mock_client_class):
        """connect_to_master does nothing when running as master."""
        # Configure as master
        ServerConfig.reset()
        ServerConfig.initialize(role=Role.MASTER)

        asyncio.run(connect_to_master())

        # Verify no client was created
        mock_client_class.assert_not_called()

    @patch("app.replication.ReplicationClient")
    def test_connect_to_master_handles_error(self, mock_client_class):
        """connect_to_master handles handshake errors gracefully."""
        # Configure as slave
        ServerConfig.reset()
        ServerConfig.initialize(
            role=Role.SLAVE,
            master_host="localhost",
            master_port=6379,
        )

        mock_client = AsyncMock()
        mock_client.start_handshake.side_effect = ConnectionError("Failed")
        mock_client_class.return_value = mock_client

        # Should not raise exception
        asyncio.run(connect_to_master())

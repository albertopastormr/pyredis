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
        """send_ping correctly sends PING command and reads PONG response."""
        # Mock the connection
        mock_reader = AsyncMock()
        mock_reader.readuntil = AsyncMock(return_value=b"+PONG\r\n")
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
        
        # Verify response was read
        mock_reader.readuntil.assert_called_once()

    @patch("asyncio.open_connection")
    def test_send_replconf_listening_port(self, mock_open_connection, replication_client):
        """send_replconf_listening_port sends correct command and reads response."""
        # Mock the connection
        mock_reader = AsyncMock()
        mock_reader.readuntil = AsyncMock(return_value=b"+OK\r\n")
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        asyncio.run(replication_client.connect())
        asyncio.run(replication_client.send_replconf_listening_port(6380))

        # Verify REPLCONF was written
        assert mock_writer.write.call_count == 1
        written_data = mock_writer.write.call_args[0][0]
        
        # Verify RESP format: *3\r\n$8\r\nREPLCONF\r\n$14\r\nlistening-port\r\n$4\r\n6380\r\n
        assert written_data == b"*3\r\n$8\r\nREPLCONF\r\n$14\r\nlistening-port\r\n$4\r\n6380\r\n"
        mock_reader.readuntil.assert_called_once()

    @patch("asyncio.open_connection")
    def test_send_replconf_capa(self, mock_open_connection, replication_client):
        """send_replconf_capa sends correct command and reads response."""
        # Mock the connection
        mock_reader = AsyncMock()
        mock_reader.readuntil = AsyncMock(return_value=b"+OK\r\n")
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        asyncio.run(replication_client.connect())
        asyncio.run(replication_client.send_replconf_capa())

        # Verify REPLCONF was written
        assert mock_writer.write.call_count == 1
        written_data = mock_writer.write.call_args[0][0]
        
        # Verify RESP format: *3\r\n$8\r\nREPLCONF\r\n$4\r\ncapa\r\n$6\r\npsync2\r\n
        assert written_data == b"*3\r\n$8\r\nREPLCONF\r\n$4\r\ncapa\r\n$6\r\npsync2\r\n"
        mock_reader.readuntil.assert_called_once()

    def test_send_replconf_requires_connection(self, replication_client):
        """send_replconf methods raise error when not connected."""
        with pytest.raises(RuntimeError, match="Not connected to master"):
            asyncio.run(replication_client.send_replconf_listening_port(6380))
        
        with pytest.raises(RuntimeError, match="Not connected to master"):
            asyncio.run(replication_client.send_replconf_capa())

    @patch("asyncio.open_connection")
    def test_replconf_validates_response(self, mock_open_connection, replication_client):
        """REPLCONF methods validate master response."""
        # Mock the connection with bad response
        mock_reader = AsyncMock()
        mock_reader.readuntil = AsyncMock(return_value=b"-ERR unknown command\r\n")
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        asyncio.run(replication_client.connect())
        
        # Should raise error for bad response
        with pytest.raises(RuntimeError, match="Unexpected response"):
            asyncio.run(replication_client.send_replconf_listening_port(6380))

    @patch("asyncio.open_connection")
    def test_send_psync(self, mock_open_connection, replication_client):
        """send_psync sends correct command and reads FULLRESYNC response."""
        # Mock the connection
        mock_reader = AsyncMock()
        mock_reader.readuntil = AsyncMock(return_value=b"+FULLRESYNC 8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb 0\r\n")
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        asyncio.run(replication_client.connect())
        asyncio.run(replication_client.send_psync())

        # Verify PSYNC was written
        assert mock_writer.write.call_count == 1
        written_data = mock_writer.write.call_args[0][0]
        
        # Verify RESP format: *3\r\n$5\r\nPSYNC\r\n$1\r\n?\r\n$2\r\n-1\r\n
        assert written_data == b"*3\r\n$5\r\nPSYNC\r\n$1\r\n?\r\n$2\r\n-1\r\n"
        mock_reader.readuntil.assert_called_once()

    def test_send_psync_requires_connection(self, replication_client):
        """send_psync raises error when not connected."""
        with pytest.raises(RuntimeError, match="Not connected to master"):
            asyncio.run(replication_client.send_psync())

    @patch("asyncio.open_connection")
    def test_psync_validates_response(self, mock_open_connection, replication_client):
        """PSYNC validates FULLRESYNC response."""
        # Mock the connection with bad response
        mock_reader = AsyncMock()
        mock_reader.readuntil = AsyncMock(return_value=b"-ERR unknown command\r\n")
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)

        asyncio.run(replication_client.connect())
        
        # Should raise error for bad response
        with pytest.raises(RuntimeError, match="Unexpected response"):
            asyncio.run(replication_client.send_psync())

    @patch("asyncio.open_connection")
    @patch("app.replication.ServerConfig.get_listening_port")
    def test_start_handshake(self, mock_get_port, mock_open_connection, replication_client):
        """start_handshake performs full handshake: PING + REPLCONF × 2 + PSYNC."""
        mock_reader = AsyncMock()
        # Mock responses: PONG, OK, OK, FULLRESYNC
        mock_reader.readuntil = AsyncMock(side_effect=[
            b"+PONG\r\n",
            b"+OK\r\n",
            b"+OK\r\n",
            b"+FULLRESYNC 8371b4fb1155b71f4a04d3e1bc3e18c4a990aeeb 0\r\n"
        ])
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_open_connection.return_value = (mock_reader, mock_writer)
        mock_get_port.return_value = 6380

        asyncio.run(replication_client.start_handshake())

        # Verify connection was made
        mock_open_connection.assert_called_once_with("localhost", 6379)
        
        # Verify commands were sent: PING + REPLCONF x 2 + PSYNC
        assert mock_writer.write.call_count == 4
        
        # Verify PING
        ping_data = mock_writer.write.call_args_list[0][0][0]
        assert ping_data == b"*1\r\n$4\r\nPING\r\n"
        
        # Verify REPLCONF listening-port
        replconf_port_data = mock_writer.write.call_args_list[1][0][0]
        assert b"REPLCONF" in replconf_port_data
        assert b"listening-port" in replconf_port_data
        
        # Verify REPLCONF capa
        replconf_capa_data = mock_writer.write.call_args_list[2][0][0]
        assert b"REPLCONF" in replconf_capa_data
        assert b"psync2" in replconf_capa_data
        
        # Verify PSYNC
        psync_data = mock_writer.write.call_args_list[3][0][0]
        assert b"PSYNC" in psync_data
        assert b"?" in psync_data
        assert b"-1" in psync_data
        
        # Verify all responses were read (PONG + OK + OK + FULLRESYNC)
        assert mock_reader.readuntil.call_count == 4


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

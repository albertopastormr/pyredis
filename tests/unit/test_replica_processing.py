"""Unit tests for replica command processing with from_replication flag."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import ReplicationConfig, Role, ServerConfig
from app.handler import execute_command
from app.replica_manager import ReplicaManager


class TestFromReplicationFlag:
    """Test the from_replication parameter in execute_command."""

    def setup_method(self):
        """Set up test fixtures."""
        # Configure as master for these tests
        ServerConfig.initialize(role=Role.MASTER, listening_port=6379)
        ReplicaManager.reset()

    def teardown_method(self):
        """Clean up after tests."""
        ReplicaManager.reset()

    def test_from_replication_false_propagates_command(self):
        """Test that commands with from_replication=False are propagated."""
        # Add a mock replica
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        
        ReplicaManager.add_replica("test_replica", mock_writer)
        
        # Execute a write command with from_replication=False
        result = asyncio.run(
            execute_command(["SET", "key", "value"], from_replication=False)
        )
        
        # Verify command was propagated
        assert mock_writer.write.called
        assert result == {"ok": "OK"}

    def test_from_replication_true_skips_propagation(self):
        """Test that commands with from_replication=True are NOT propagated."""
        # Add a mock replica
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        
        ReplicaManager.add_replica("test_replica", mock_writer)
        
        # Execute a write command with from_replication=True
        result = asyncio.run(
            execute_command(["SET", "key", "value"], from_replication=True)
        )
        
        # Verify command was NOT propagated
        assert not mock_writer.write.called
        assert result == {"ok": "OK"}

    def test_from_replication_updates_storage(self):
        """Test that from_replication commands still update storage."""
        # Execute SET with from_replication=True
        asyncio.run(
            execute_command(["SET", "foo", "bar"], from_replication=True)
        )
        
        # Verify storage was updated by executing GET
        result = asyncio.run(execute_command(["GET", "foo"]))
        assert result == "bar"

    def test_read_commands_not_affected(self):
        """Test that read commands work the same regardless of from_replication."""
        # Set a value first
        asyncio.run(execute_command(["SET", "key", "value"]))
        
        # GET with from_replication=False
        result1 = asyncio.run(execute_command(["GET", "key"], from_replication=False))
        
        # GET with from_replication=True
        result2 = asyncio.run(execute_command(["GET", "key"], from_replication=True))
        
        # Both should return the same value
        assert result1 == "value"
        assert result2 == "value"

    def test_from_replication_with_replica_role(self):
        """Test that replicas don't propagate even with from_replication=False."""
        # Configure as replica
        ServerConfig.initialize(
            role=Role.SLAVE,
            master_host="localhost",
            master_port=6380,
            listening_port=6379
        )
        
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        ReplicaManager.add_replica("test", mock_writer)
        
        # Execute write command as replica
        asyncio.run(execute_command(["SET", "key", "value"], from_replication=False))
        
        # Replica should not propagate (only master propagates)
        assert not mock_writer.write.called


class TestReplicaManager:
    """Test ReplicaManager with from_replication context."""

    def setup_method(self):
        """Set up test fixtures."""
        ReplicaManager.reset()

    def teardown_method(self):
        """Clean up."""
        ReplicaManager.reset()

    def test_propagate_command_encoding(self):
        """Test that propagate_command encodes correctly."""
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        
        ReplicaManager.add_replica("replica1", mock_writer)
        
        # Propagate a command
        asyncio.run(ReplicaManager.propagate_command("SET", ["foo", "bar"]))
        
        # Check that write was called
        assert mock_writer.write.called
        
        # Verify RESP array encoding
        call_args = mock_writer.write.call_args[0][0]
        assert b"*3\r\n" in call_args  # Array of 3 elements
        assert b"$3\r\nSET\r\n" in call_args
        assert b"$3\r\nfoo\r\n" in call_args
        assert b"$3\r\nbar\r\n" in call_args

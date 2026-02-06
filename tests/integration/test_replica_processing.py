"""Integration tests for replica command processing."""

import asyncio

import pytest

from app.config import ReplicationConfig, Role, ServerConfig
from app.replica_manager import ReplicaManager
from tests.helpers import execute_command


class TestReplicaCommandProcessing:
    """Integration tests for replica processing of propagated commands."""

    def setup_method(self):
        """Set up test environment."""
        # Start as master
        ServerConfig.initialize(role=Role.MASTER, listening_port=6379)
        ReplicaManager.reset()

    def teardown_method(self):
        """Clean up."""
        ReplicaManager.reset()

    def test_propagated_command_updates_storage(self):
        """Test that propagated commands update replica storage."""
        # Execute command as if from replication
        result = execute_command(["SET", "replicated_key", "replicated_value"], from_replication=True)
        
        # Verify it was stored
        stored_value = execute_command(["GET", "replicated_key"])
        assert stored_value == "replicated_value"

    def test_propagated_command_returns_result(self):
        """Test that propagated commands still return results (even if not sent)."""
        result = execute_command(["SET", "key", "value"], from_replication=True)
        assert result == {"ok": "OK"}

    def test_multiple_propagated_commands(self):
        """Test processing multiple propagated commands in sequence."""
        # Simulate multiple commands from master
        execute_command(["SET", "key1", "value1"], from_replication=True)
        execute_command(["SET", "key2", "value2"], from_replication=True)
        execute_command(["SET", "key3", "value3"], from_replication=True)
        
        # Verify all were stored
        assert execute_command(["GET", "key1"]) == "value1"
        assert execute_command(["GET", "key2"]) == "value2"
        assert execute_command(["GET", "key3"]) == "value3"

    def test_propagated_incr_command(self):
        """Test that INCR commands work when propagated."""
        # Set initial value
        execute_command(["SET", "counter", "0"], from_replication=True)
        
        # Increment via propagation
        result = execute_command(["INCR", "counter"], from_replication=True)
        assert result == 1
        
        # Verify storage
        assert execute_command(["GET", "counter"]) == "1"

    def test_propagated_list_commands(self):
        """Test that list commands work when propagated."""
        # RPUSH via propagation
        execute_command(["RPUSH", "mylist", "item1"], from_replication=True)
        execute_command(["RPUSH", "mylist", "item2"], from_replication=True)
        
        # Verify list contents
        result = execute_command(["LRANGE", "mylist", "0", "-1"])
        assert result == ["item1", "item2"]

    def test_no_double_propagation(self):
        """Test that propagated commands don't get re-propagated."""
        from unittest.mock import MagicMock, AsyncMock
        
        # Add a mock replica
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        ReplicaManager.add_replica("replica", mock_reader, mock_writer)
        
        # Execute command with from_replication=True
        execute_command(["SET", "key", "value"], from_replication=True)
        
        # Verify it was NOT propagated (no write calls)
        assert not mock_writer.write.called


class TestMasterToReplicaPropagation:
    """Test end-to-end propagation from master to replicas."""

    def setup_method(self):
        """Set up as master."""
        ServerConfig.initialize(role=Role.MASTER, listening_port=6379)
        ReplicaManager.reset()

    def teardown_method(self):
        """Clean up."""
        ReplicaManager.reset()

    def test_master_propagates_to_multiple_replicas(self):
        """Test that master propagates to all connected replicas."""
        from unittest.mock import MagicMock, AsyncMock
        
        # Create mock replicas
        reader1 = MagicMock()
        replica1 = MagicMock()
        replica1.write = MagicMock()
        replica1.drain = AsyncMock()
        
        reader2 = MagicMock()
        replica2 = MagicMock()
        replica2.write = MagicMock()
        replica2.drain = AsyncMock()
        
        # Register replicas
        ReplicaManager.add_replica("replica1", reader1, replica1)
        ReplicaManager.add_replica("replica2", reader2, replica2)
        
        # Execute write command (not from replication)
        execute_command(["SET", "key", "value"], from_replication=False)
        
        # Both replicas should receive the command
        assert replica1.write.called
        assert replica2.write.called

    def test_client_command_propagated_replica_command_not(self):
        """Test that client commands propagate but replica commands don't."""
        from unittest.mock import MagicMock, AsyncMock
        
        mock_reader = MagicMock()
        mock_replica = MagicMock()
        mock_replica.write = MagicMock()
        mock_replica.drain = AsyncMock()
        ReplicaManager.add_replica("replica", mock_reader, mock_replica)
        
        # Client command (from_replication=False) - should propagate
        execute_command(["SET", "client_key", "value"], from_replication=False)
        assert mock_replica.write.call_count == 1
        
        # Replica command (from_replication=True) - should NOT propagate
        execute_command(["SET", "replica_key", "value"], from_replication=True)
        assert mock_replica.write.call_count == 1  # Still 1, not 2

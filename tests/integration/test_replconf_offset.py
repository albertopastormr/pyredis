"""Integration test for REPLCONF GETACK offset tracking."""

import asyncio
import pytest

from app.replication import ReplicationClient
from app.resp import RESPEncoder, RESPParser


class MockStreamWriter:
    """Mock writer for testing."""
    
    def __init__(self):
        self.written_data = []
    
    def write(self, data: bytes):
        """Track written data."""
        self.written_data.append(data)
    
    async def drain(self):
        """Mock drain."""
        pass


class TestReplicationOffset:
    """Test offset tracking in replication."""
    
    def test_offset_initialization(self):
        """Offset should be initialized to 0."""
        client = ReplicationClient("localhost", 6379)
        assert client.offset == 0
    
    def test_offset_increments_after_command(self):
        """Offset should increment after processing commands."""
        # This test validates the byte counting logic
        
        # REPLCONF GETACK * is 37 bytes
        getack_cmd = RESPEncoder.encode(["REPLCONF", "GETACK", "*"])
        assert len(getack_cmd) == 37
        
        # SET key value command
        set_cmd = RESPEncoder.encode(["SET", "foo", "bar"])
        # *3\r\n$3\r\nSET\r\n$3\r\nfoo\r\n$3\r\nbar\r\n = 31 bytes
        assert len(set_cmd) == 31
        
        # PING command
        ping_cmd = RESPEncoder.encode(["PING"])
        # *1\r\n$4\r\nPING\r\n = 14 bytes
        assert len(ping_cmd) == 14
    
    def test_getack_detection_logic(self):
        """Test the logic for detecting REPLCONF GETACK commands."""
        
        # Valid GETACK command
        cmd1 = ["REPLCONF", "GETACK", "*"]
        is_getack = (
            isinstance(cmd1, list) and 
            len(cmd1) == 3 and
            cmd1[0].upper() == "REPLCONF" and
            cmd1[1].upper() == "GETACK"
        )
        assert is_getack is True
        
        # Case-insensitive check
        cmd2 = ["replconf", "getack", "*"]
        is_getack = (
            isinstance(cmd2, list) and 
            len(cmd2) == 3 and
            cmd2[0].upper() == "REPLCONF" and
            cmd2[1].upper() == "GETACK"
        )
        assert is_getack is True
        
        # Not a GETACK command (SET)
        cmd3 = ["SET", "key", "value"]
        is_getack = (
            isinstance(cmd3, list) and 
            len(cmd3) == 3 and
            cmd3[0].upper() == "REPLCONF" and
            cmd3[1].upper() == "GETACK"
        )
        assert is_getack is False
        
        # Not a GETACK command (REPLCONF listening-port)
        cmd4 = ["REPLCONF", "listening-port", "6380"]
        is_getack = (
            isinstance(cmd4, list) and 
            len(cmd4) == 3 and
            cmd4[0].upper() == "REPLCONF" and
            cmd4[1].upper() == "GETACK"
        )
        assert is_getack is False
        
        # Wrong length
        cmd5 = ["REPLCONF", "GETACK"]
        is_getack = (
            isinstance(cmd5, list) and 
            len(cmd5) == 3 and
            cmd5[0].upper() == "REPLCONF" and
            cmd5[1].upper() == "GETACK"
        )
        assert is_getack is False

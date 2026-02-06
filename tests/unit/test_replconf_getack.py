"""Unit tests for REPLCONF GETACK functionality."""

import pytest

from app.resp import RESPEncoder, RESPParser


class TestReplconfGetack:
    """Test REPLCONF GETACK command encoding and parsing."""

    def test_replconf_getack_encoding(self):
        """Verify REPLCONF GETACK * uses correct RESP encoding."""
        # Encode the command
        encoded = RESPEncoder.encode(["REPLCONF", "GETACK", "*"])
        
        # Verify exact RESP format
        assert encoded == b"*3\r\n$8\r\nREPLCONF\r\n$6\r\nGETACK\r\n$1\r\n*\r\n"
        
        # Break down the format
        assert encoded.startswith(b"*3\r\n")  # Array with 3 elements
        assert b"$8\r\nREPLCONF\r\n" in encoded  # Command name
        assert b"$6\r\nGETACK\r\n" in encoded  # Subcommand
        assert b"$1\r\n*\r\n" in encoded  # Argument

    def test_replconf_getack_parsing(self):
        """Verify REPLCONF GETACK can be parsed correctly."""
        # Raw RESP encoded command
        raw_data = b"*3\r\n$8\r\nREPLCONF\r\n$6\r\nGETACK\r\n$1\r\n*\r\n"
        
        # Parse the command
        command = RESPParser.parse(raw_data)
        
        # Verify parsed result
        assert isinstance(command, list)
        assert len(command) == 3
        assert command[0].upper() == "REPLCONF"
        assert command[1].upper() == "GETACK"
        assert command[2] == "*"

    def test_replconf_ack_encoding(self):
        """Verify REPLCONF ACK <offset> uses correct RESP encoding."""
        # Encode the ACK response with offset 0
        encoded = RESPEncoder.encode(["REPLCONF", "ACK", "0"])
        assert encoded == b"*3\r\n$8\r\nREPLCONF\r\n$3\r\nACK\r\n$1\r\n0\r\n"
        
        # Encode the ACK response with offset 123
        encoded = RESPEncoder.encode(["REPLCONF", "ACK", "123"])
        assert encoded == b"*3\r\n$8\r\nREPLCONF\r\n$3\r\nACK\r\n$3\r\n123\r\n"

    def test_replconf_ack_parsing(self):
        """Verify REPLCONF ACK can be parsed correctly."""
        # Raw RESP encoded ACK with offset 123
        raw_data = b"*3\r\n$8\r\nREPLCONF\r\n$3\r\nACK\r\n$3\r\n123\r\n"
        
        # Parse the command
        command = RESPParser.parse(raw_data)
        
        # Verify parsed result
        assert isinstance(command, list)
        assert len(command) == 3
        assert command[0].upper() == "REPLCONF"
        assert command[1].upper() == "ACK"
        assert command[2] == "123"

    def test_getack_command_byte_size(self):
        """Calculate byte size of REPLCONF GETACK command."""
        # This is important for offset tracking
        encoded = RESPEncoder.encode(["REPLCONF", "GETACK", "*"])
        
        # The byte size should be 37 bytes
        assert len(encoded) == 37

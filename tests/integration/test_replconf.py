"""Integration tests for REPLCONF command."""

import pytest

from app.resp import RESPEncoder
from tests.helpers import execute_command


class TestReplconfIntegration:
    """Integration tests for REPLCONF command."""

    def test_replconf_listening_port(self):
        """Test REPLCONF listening-port returns OK."""
        result = execute_command(["REPLCONF", "listening-port", "6380"])

        # Should return OK (as dict for simple string encoding)
        assert result == {"ok": "OK"}

    def test_replconf_capa_psync2(self):
        """Test REPLCONF capa psync2 returns OK."""
        result = execute_command(["REPLCONF", "capa", "psync2"])

        assert result == {"ok": "OK"}

    def test_replconf_accepts_any_subcommand(self):
        """Test REPLCONF accepts various subcommands."""
        # Test unknown subcommand (should still return OK for now)
        result = execute_command(["REPLCONF", "unknown", "value"])
        assert result == {"ok": "OK"}

    def test_replconf_no_arguments_error(self):
        """Test REPLCONF without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            execute_command(["REPLCONF"])

    def test_replconf_resp_encoding(self):
        """Test REPLCONF RESP encoding format."""
        # Test listening-port encoding
        encoded = RESPEncoder.encode(["REPLCONF", "listening-port", "6380"])
        assert encoded == b"*3\r\n$8\r\nREPLCONF\r\n$14\r\nlistening-port\r\n$4\r\n6380\r\n"

        # Test capa encoding
        encoded = RESPEncoder.encode(["REPLCONF", "capa", "psync2"])
        assert encoded == b"*3\r\n$8\r\nREPLCONF\r\n$4\r\ncapa\r\n$6\r\npsync2\r\n"

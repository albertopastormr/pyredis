"""Unit tests for REPLCONF command."""

import asyncio

import pytest

from app.commands.replconf import ReplconfCommand


@pytest.fixture
def replconf_cmd():
    """Fixture providing a ReplconfCommand instance."""
    return ReplconfCommand()


class TestReplconfCommand:
    """Test REPLCONF command implementation."""

    def test_name(self, replconf_cmd):
        """Command name is 'REPLCONF'."""
        assert replconf_cmd.name == "REPLCONF"

    def test_replconf_listening_port(self, replconf_cmd):
        """REPLCONF listening-port returns OK."""
        result = asyncio.run(replconf_cmd.execute(["listening-port", "6380"]))
        assert result == {"ok": "OK"}

    def test_replconf_capa(self, replconf_cmd):
        """REPLCONF capa returns OK."""
        result = asyncio.run(replconf_cmd.execute(["capa", "psync2"]))
        assert result == {"ok": "OK"}

    def test_replconf_no_args(self, replconf_cmd):
        """REPLCONF without arguments raises error."""
        with pytest.raises(ValueError, match="wrong number of arguments"):
            asyncio.run(replconf_cmd.execute([]))

    def test_replconf_accepts_any_subcommand(self, replconf_cmd):
        """REPLCONF accepts any subcommand for now."""
        # Test various possible subcommands
        result = asyncio.run(replconf_cmd.execute(["unknown-subcommand", "arg1", "arg2"]))
        assert result == {"ok": "OK"}
        
        result = asyncio.run(replconf_cmd.execute(["some-future-command"]))
        assert result == {"ok": "OK"}

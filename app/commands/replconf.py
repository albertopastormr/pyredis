"""REPLCONF command implementation."""

from typing import Any

from .base import BaseCommand


class ReplconfCommand(BaseCommand):
    """
    REPLCONF command - Configuration command for replication.
    
    Used during replica-to-master handshake to:
    - Inform master of replica's listening port
    - Inform master of replica's capabilities
    """

    @property
    def name(self) -> str:
        return "REPLCONF"

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute REPLCONF command.

        Args:
            args: Subcommand and arguments
                  - listening-port <PORT>
                  - capa <capability>

        Returns:
            OK response (we ignore arguments for now)
        """
        self.validate_args(args, min_args=1)
        
        return {"ok": "OK"}

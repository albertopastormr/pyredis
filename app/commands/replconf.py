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

        subcommand = args[0].upper()

        # Handle REPLCONF ACK <offset>
        if subcommand == "ACK":
            if len(args) < 2:
                # Should we raise error? Redis just ignores partial commands sometimes.
                # But let's be strict or lenient?
                # For this stage, let's assume valid command.
                return {"no_response": True}

            try:
                offset = int(args[1])
                if connection_id:
                    from ..replica_manager import ReplicaManager

                    await ReplicaManager.update_replica_ack(connection_id, offset)
            except ValueError:
                pass

            # Master does not respond to REPLCONF ACK
            return {"no_response": True}

        return {"ok": "OK"}

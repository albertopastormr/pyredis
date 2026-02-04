"""PSYNC command implementation."""

from typing import Any

from app.config import ServerConfig

from .base import BaseCommand


class PsyncCommand(BaseCommand):
    """
    PSYNC command - Synchronization command for replication.
    
    Used by replica to request synchronization from master.
    Master responds with FULLRESYNC for initial sync.
    """

    @property
    def name(self) -> str:
        return "PSYNC"

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute PSYNC command.

        Args:
            args: [replication_id, offset]
                  - For initial sync: ["?", "-1"]

        Returns:
            FULLRESYNC response with master's replication ID and offset
        """
        self.validate_args(args, min_args=2, max_args=2)
        
        repl_config = ServerConfig.get_replication_config()
        repl_id = repl_config.master_replid
        offset = repl_config.master_repl_offset
        
        return f"FULLRESYNC {repl_id} {offset}"

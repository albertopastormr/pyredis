"""PSYNC command implementation."""

from typing import Any

from app.config import ServerConfig
from app.rdb import EMPTY_RDB

from .base import BaseCommand


class PsyncCommand(BaseCommand):
    """
    PSYNC command - Synchronization command for replication.
    
    Used by replica to request synchronization from master.
    Master responds with FULLRESYNC for initial sync, followed by RDB file.
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
            Special response dict with FULLRESYNC message and RDB file
        """
        self.validate_args(args, min_args=2, max_args=2)
        
        repl_config = ServerConfig.get_replication_config()
        repl_id = repl_config.master_replid
        offset = repl_config.master_repl_offset
        
        # Return special response with RDB file
        return {
            "fullresync": {
                "replid": repl_id,
                "offset": offset,
                "rdb": EMPTY_RDB
            }
        }

"""INFO command implementation."""

from typing import Any

from ..config import ServerConfig
from .base import BaseCommand


class InfoCommand(BaseCommand):
    """
    INFO command - Returns server information and statistics.

    Supports optional section parameter to filter output.
    For now, only supports the 'replication' section.
    """

    @property
    def name(self) -> str:
        return "INFO"

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute INFO command.

        Args:
            args: Optional section name (e.g., 'replication')

        Returns:
            Bulk string containing requested information
        """
        self.validate_args(args, min_args=0, max_args=1)

        # Get section parameter (default: all sections)
        section = args[0].lower() if args else None

        # For now, we only support the replication section
        if section is None or section == "replication":
            return self._get_replication_info()

        # If specific section requested but not supported, return empty
        return ""

    def _get_replication_info(self) -> str:
        """
        Build replication section information.

        Returns:
            String with replication info in key:value format
        """
        repl_config = ServerConfig.get_replication_config()

        lines = [
            "# Replication",
            f"role:{repl_config.role.value}",
            f"master_replid:{repl_config.master_replid}",
            f"master_repl_offset:{repl_config.master_repl_offset}",
        ]
        return "\n".join(lines)

"""ECHO command implementation."""

from typing import Any

from .base import BaseCommand


class EchoCommand(BaseCommand):
    """
    ECHO command - Returns the given string.

    Syntax: ECHO message
    """

    @property
    def name(self) -> str:
        return "ECHO"

    async def execute(self, args: list[str]) -> Any:
        """
        Execute ECHO command.

        Args:
            args: Message to echo (exactly 1 argument required)

        Returns:
            The message as a bulk string
        """
        self.validate_args(args, min_args=1, max_args=1)
        return args[0]

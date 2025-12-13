"""
Command registry - Auto-discovers and registers all commands.

This module provides a central registry for all Redis commands.
"""

from typing import Any

from .base import BaseCommand
from .blpop import BlpopCommand
from .echo import EchoCommand
from .get import GetCommand
from .llen import LlenCommand
from .lpop import LpopCommand
from .lpush import LpushCommand
from .lrange import LrangeCommand
from .ping import PingCommand
from .rpush import RpushCommand
from .set import SetCommand
from .type import TypeCommand


class CommandRegistry:
    """Central registry for all Redis commands."""

    _commands: dict[str, type[BaseCommand]] = {}

    @classmethod
    def register(cls, command_class: type[BaseCommand]) -> None:
        """
        Register a command class.

        Args:
            command_class: Command class to register
        """
        # Create temporary instance to get the name
        instance = command_class()
        cls._commands[instance.name.upper()] = command_class

    @classmethod
    def execute(cls, command_name: str, args: list[str]) -> Any:
        """
        Execute a command by name.

        Args:
            command_name: Name of the command (case-insensitive)
            args: Command arguments

        Returns:
            Command result (to be encoded by RESPEncoder)

        Raises:
            ValueError: If command is unknown
        """
        command_class = cls._commands.get(command_name.upper())

        if command_class is None:
            raise ValueError(f"ERR unknown command '{command_name}'")

        # Create instance and execute
        command = command_class()
        return command.execute(args)

    @classmethod
    def get_all_commands(cls) -> list[str]:
        """Get list of all registered command names."""
        return sorted(cls._commands.keys())


# Auto-register all commands
CommandRegistry.register(PingCommand)
CommandRegistry.register(EchoCommand)
CommandRegistry.register(SetCommand)
CommandRegistry.register(GetCommand)
CommandRegistry.register(RpushCommand)
CommandRegistry.register(LrangeCommand)
CommandRegistry.register(LpushCommand)
CommandRegistry.register(LlenCommand)
CommandRegistry.register(LpopCommand)
CommandRegistry.register(BlpopCommand)
CommandRegistry.register(TypeCommand)


__all__ = [
    "CommandRegistry",
    "BaseCommand",
    "PingCommand",
    "EchoCommand",
    "SetCommand",
    "GetCommand",
    "RpushCommand",
    "LrangeCommand",
    "LpushCommand",
    "LlenCommand",
    "LpopCommand",
    "BlpopCommand",
]

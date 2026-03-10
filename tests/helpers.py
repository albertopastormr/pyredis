"""Test helpers - provides sync wrappers for async handler functions."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.handler import execute_command as async_execute_command


def execute_command(args, from_replication=False, connection_id=None):
    """
    Synchronous wrapper for execute_command.

    Tests import this to call the async execute_command synchronously.

    Args:
        args: Command and arguments as list
        from_replication: Whether command is from replication
        connection_id: Optional connection identifier

    Returns:
        Command execution result
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        async_execute_command(args, from_replication=from_replication, connection_id=connection_id)
    )


def execute_command_with_mock_writer(args, connection_id=None):
    """Execute command returning both result and mock writer for inspecting outputs."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    writer = MagicMock()
    writer.drain = AsyncMock()
    result = loop.run_until_complete(
        async_execute_command(
            args, from_replication=False, connection_id=connection_id, writer=writer
        )
    )
    return result, writer

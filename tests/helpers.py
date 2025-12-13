"""Test helpers - provides sync wrappers for async handler functions."""

import asyncio

from app.handler import execute_command as async_execute_command


def execute_command(args):
    """
    Synchronous wrapper for execute_command.

    Tests import this to call the async execute_command synchronously.

    Args:
        args: Command and arguments as list

    Returns:
        Command execution result
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(async_execute_command(args))

"""Client connection handler - RESP protocol layer."""

import asyncio
from typing import Any

from .commands import CommandRegistry
from .resp import RESPEncoder, RESPParser


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """
    Handle a single client connection.

    Manages the RESP protocol communication for one client session.
    Parses incoming commands, executes them, and sends responses.

    Args:
        reader: Async stream reader for incoming data
        writer: Async stream writer for outgoing data
    """
    addr = writer.get_extra_info("peername")
    print(f"[{addr}] Client connected")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break

            print(f"[{addr}] Received {len(data)} bytes")

            try:
                command = RESPParser.parse(data)
                print(f"[{addr}] Parsed command: {command}")

                response = await execute_command(command)

                response_bytes = RESPEncoder.encode(response)
                writer.write(response_bytes)
                await writer.drain()

            except ValueError as e:
                print(f"[{addr}] Error: {e}")
                error_resp = RESPEncoder.encode({"error": str(e)})
                writer.write(error_resp)
                await writer.drain()

    except asyncio.CancelledError:
        print(f"[{addr}] Connection cancelled")
    except Exception as e:
        print(f"[{addr}] Unexpected error: {e}")
    finally:
        print(f"[{addr}] Closing connection")
        writer.close()
        await writer.wait_closed()


async def execute_command(args: list[str]) -> Any:
    """
    Execute a command asynchronously.

    Single unified interface for command execution.

    Args:
        args: Command and arguments as list of strings (command name included)

    Returns:
        Result from command execution

    Raises:
        ValueError: For command errors
    """
    if not isinstance(args, list) or len(args) == 0:
        raise ValueError("Invalid command format")

    command_name = args[0]
    command_args = args[1:]

    command_class = CommandRegistry._commands.get(command_name.upper())

    if not command_class:
        raise ValueError(f"ERR unknown command '{command_name}'")

    command_obj = command_class()
    return await command_obj.execute(command_args)

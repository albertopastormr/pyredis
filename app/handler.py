"""Client connection handler - RESP protocol layer."""

import asyncio
from typing import Any

from .commands import CommandRegistry
from .resp import RESPEncoder, RESPParser
from .transaction import get_transaction_context, remove_transaction_context


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

                response = await execute_command(command, connection_id=addr)

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
        remove_transaction_context(connection_id=addr)
        writer.close()
        await writer.wait_closed()


async def execute_command(args: list[str], connection_id: Any = None) -> Any:
    """
    Execute a command asynchronously.

    Single unified interface for command execution.
    Handles transaction queuing when in MULTI mode.

    Args:
        args: Command and arguments as list of strings (command name included)
        connection_id: Connection identifier for transaction tracking

    Returns:
        Result from command execution, or {"queued": "QUEUED"} if command was queued

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

    transaction_ctx = None
    if connection_id is not None:
        transaction_ctx = get_transaction_context(connection_id)

    if transaction_ctx and transaction_ctx.in_transaction and not command_obj.bypasses_transaction_queue:
        transaction_ctx.queue_command(command_name, command_args)
        return {"queued": "QUEUED"}

    return await command_obj.execute(command_args, connection_id=connection_id)

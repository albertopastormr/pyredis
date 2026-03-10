"""Client connection handler - RESP protocol layer."""

import asyncio
import logging
from typing import Any

from .commands import CommandRegistry
from .config import ServerConfig
from .pubsub import get_pubsub_context, remove_pubsub_context
from .replica_manager import ReplicaManager
from .resp import RESPEncoder, RESPParser
from .transaction import get_transaction_context, remove_transaction_context

logger = logging.getLogger(__name__)


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
    logger.info(f"[{addr}] Client connected")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break

            logger.debug(f"[{addr}] Received {len(data)} bytes")

            try:
                command = RESPParser.parse(data)
                logger.debug(f"[{addr}] Parsed command: {command}")

                response = await execute_command(
                    command, connection_id=addr, reader=reader, writer=writer
                )

                response_bytes = RESPEncoder.encode(response)
                writer.write(response_bytes)
                await writer.drain()

            except ValueError as e:
                logger.error(f"[{addr}] Error: {e}")
                error_resp = RESPEncoder.encode({"error": str(e)})
                writer.write(error_resp)
                await writer.drain()

    except asyncio.CancelledError:
        logger.info(f"[{addr}] Connection cancelled")
    except Exception as e:
        logger.error(f"[{addr}] Unexpected error: {e}")
    finally:
        logger.info(f"[{addr}] Closing connection")
        remove_transaction_context(connection_id=addr)
        remove_pubsub_context(connection_id=addr)
        ReplicaManager.remove_replica(addr)  # Clean up replica if it was registered
        writer.close()
        await writer.wait_closed()


async def execute_command(
    args: list[str],
    connection_id: Any = None,
    reader: asyncio.StreamReader = None,
    writer: asyncio.StreamWriter = None,
    from_replication: bool = False,
) -> Any:
    """
    Execute a command asynchronously.

    Single unified interface for command execution.
    Handles transaction queuing when in MULTI mode.

    Args:
        args: Command and arguments as list of strings (command name included)
        connection_id: Connection identifier for transaction tracking
        reader: Optional stream reader for replica registration
        writer: Optional stream writer for replica registration
        from_replication: True if command is propagated from master (suppresses response)

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

    # Subscribed mode check
    if connection_id is not None:
        pubsub_ctx = get_pubsub_context(connection_id)

        # Inject the writer whenever we have it (allows message delivery)
        if writer is not None and pubsub_ctx.writer is None:
            pubsub_ctx.writer = writer

        if pubsub_ctx.is_in_subscribed_mode and not command_obj.allowed_in_subscribed_mode:
            # Replicate the exact format the Codecrafters tester allows
            return {
                "error": f"ERR Can't execute '{command_name.lower()}': only (P|S)SUBSCRIBE / (P|S)UNSUBSCRIBE / PING / QUIT / RESET are allowed in this context"
            }

    transaction_ctx = None
    if connection_id is not None:
        transaction_ctx = get_transaction_context(connection_id)

    if (
        transaction_ctx
        and transaction_ctx.in_transaction
        and not command_obj.bypasses_transaction_queue
    ):
        transaction_ctx.queue_command(command_name, command_args)
        return {"queued": "QUEUED"}

    result = await command_obj.execute(command_args, connection_id=connection_id)

    # if replica is connecting, register it
    if command_name.upper() == "PSYNC" and reader is not None and writer is not None:
        if isinstance(result, dict) and "fullresync" in result:
            ReplicaManager.add_replica(connection_id, reader, writer)
            logger.info(f"[Handler] Registered replica {connection_id}")

    # Propagate write commands to replicas (only if master and not already from replication)
    if not from_replication:
        if (
            ServerConfig.get_replication_config().role.value == "master"
            and command_obj.is_write_command
        ):
            await ReplicaManager.propagate_command(command_name, command_args)

    return result

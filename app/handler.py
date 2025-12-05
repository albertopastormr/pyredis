"""Client connection handler - RESP protocol layer."""

import asyncio
from typing import Tuple

from .resp import RESPParser, RESPEncoder
from .commands import CommandRegistry


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """
    Handle a single client connection.
    
    Manages the RESP protocol communication for one client session.
    Parses incoming commands, executes them, and sends responses.
    
    Args:
        reader: Async stream reader for incoming data
        writer: Async stream writer for outgoing data
    """
    addr = writer.get_extra_info('peername')
    print(f"[{addr}] Client connected")
    
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            
            print(f"[{addr}] Received {len(data)} bytes")
            print(f"[{addr}] Raw bytes: {data!r}")
            
            try:
                command = RESPParser.parse(data)
                print(f"[{addr}] Parsed command: {command}")
                
                response = execute_command(command)
                
                response_bytes = RESPEncoder.encode(response)
                writer.write(response_bytes)
                await writer.drain()
                
            except ValueError as e:
                print(f"[{addr}] Error: {e}")
                error_resp = RESPEncoder.encode({'error': str(e)})
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


def execute_command(command) -> any:
    """
    Execute a parsed command.
    
    Args:
        command: Parsed RESP command (typically a list)
    
    Returns:
        Response value to be encoded
    """
    if not isinstance(command, list) or len(command) == 0:
        raise ValueError("Invalid command format")
    
    command_name = command[0]
    args = command[1:] if len(command) > 1 else []
    
    return CommandRegistry.execute(command_name, args)

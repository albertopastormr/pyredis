"""Redis server - connection management and server lifecycle."""

import asyncio
from collections.abc import Awaitable
from typing import Callable

from .handler import handle_client


async def start_server(
    host: str = "localhost",
    port: int = 6379,
    handler: Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]] = None,
) -> None:
    """
    Start the Redis server.

    Sets up the async server on the specified host and port,
    accepts incoming connections, and spawns handlers for each client.

    Args:
        host: Hostname to bind to (default: localhost)
        port: Port to bind to (default: 6379)
        handler: Optional custom client handler (default: handle_client)
    """
    if handler is None:
        handler = handle_client

    server = await asyncio.start_server(handler, host, port)

    addr = server.sockets[0].getsockname()
    print(f"🚀 Redis server started on {addr}")
    print("📡 Ready to accept connections...")
    print("⏹️  Press Ctrl+C to stop")

    async with server:
        await server.serve_forever()

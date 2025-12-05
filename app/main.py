"""Redis server entry point."""

import asyncio

from .server import start_server


async def main() -> None:
    """Main entry point for the Redis server."""
    await start_server(host="localhost", port=6379)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

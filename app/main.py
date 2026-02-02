"""Redis server entry point."""

import argparse
import asyncio

from .server import start_server


async def main() -> None:
    """Main entry point for the Redis server."""
    parser = argparse.ArgumentParser(description="Redis server")
    parser.add_argument(
        "--port",
        type=int,
        default=6379,
        help="Port number to bind the server to (default: 6379)",
    )
    args = parser.parse_args()

    await start_server(host="localhost", port=args.port)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

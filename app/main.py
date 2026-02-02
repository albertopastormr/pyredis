"""Redis server entry point."""

import argparse
import asyncio

from .config import Role, ServerConfig
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
    parser.add_argument(
        "--replicaof",
        type=str,
        help='Master server to replicate from (format: "host port")',
    )
    args = parser.parse_args()

    # Initialize server configuration based on replicaof flag
    if args.replicaof:
        # Parse replicaof: "host port"
        try:
            parts = args.replicaof.split()
            if len(parts) != 2:
                raise ValueError(
                    "Invalid --replicaof format. Expected: 'host port'"
                )
            master_host = parts[0]
            master_port = int(parts[1])
            
            ServerConfig.initialize(
                role=Role.SLAVE,
                master_host=master_host,
                master_port=master_port,
            )
        except ValueError as e:
            print(f"Error: {e}")
            return
    else:
        # Default to master role
        ServerConfig.initialize(role=Role.MASTER)

    await start_server(host="localhost", port=args.port)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

import asyncio


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Handle a single client connection asynchronously."""
    addr = writer.get_extra_info('peername')
    print(f"Connected by {addr}")
    
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            
            command = data.decode("utf-8").strip()
            print(f"[{addr}] Received raw: {data}")
            print(f"[{addr}] Decoded: '{command}'")
            
            writer.write(b"+PONG\r\n")
            await writer.drain()
            
    except asyncio.CancelledError:
        print(f"[{addr}] Connection cancelled")
    except Exception as e:
        print(f"[{addr}] Error: {e}")
    finally:
        print(f"Closing connection from {addr}")
        writer.close()
        await writer.wait_closed()


async def main():
    """Main async server loop."""
    server = await asyncio.start_server(
        handle_client,
        "localhost",
        6379
    )
    
    addr = server.sockets[0].getsockname()
    print(f"Server started on {addr} (async mode)")
    print("Waiting for clients... Press Ctrl+C to stop")
    
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down server...")

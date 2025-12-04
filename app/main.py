import asyncio

try:
    # When run as module: python -m app.main
    from app.resp import RESPParser, RESPEncoder
except ImportError:
    # When run as script or in different context
    from .resp import RESPParser, RESPEncoder


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """Handle a single client connection asynchronously."""
    addr = writer.get_extra_info('peername')
    print(f"Connected by {addr}")
    
    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            
            # Log received data (both raw bytes and preview)
            print(f"[{addr}] Received {len(data)} bytes")
            print(f"[{addr}] Raw bytes: {data!r}")
            
            try:
                command = RESPParser.parse(data)
                print(f"[{addr}] Parsed command: {command}")
                
                response = handle_command(command)
                writer.write(response)
                await writer.drain()
                
            except ValueError as e:
                print(f"[{addr}] Parse error: {e}")
                error_resp = RESPEncoder.encode({'error': f"Parse error: {e}"})
                writer.write(error_resp)
                await writer.drain()
            
    except asyncio.CancelledError:
        print(f"[{addr}] Connection cancelled")
    except Exception as e:
        print(f"[{addr}] Error: {e}")
    finally:
        print(f"Closing connection from {addr}")
        writer.close()
        await writer.wait_closed()


def handle_command(command):
    """Process a parsed RESP command and return the response."""
    if not isinstance(command, list) or len(command) == 0:
        return RESPEncoder.encode({'error': "Invalid command format"})
    
    cmd = command[0].upper() if isinstance(command[0], str) else str(command[0])
    
    if cmd == "PING":
        return RESPEncoder.encode({'ok': "PONG"})
    
    elif cmd == "ECHO":
        if len(command) < 2:
            return RESPEncoder.encode({'error': "ERR wrong number of arguments for 'echo' command"})
        message = command[1]
        return RESPEncoder.encode(message)
    
    else:
        return RESPEncoder.encode({'error': f"ERR unknown command '{cmd}'"})


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

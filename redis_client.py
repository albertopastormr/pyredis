#!/usr/bin/env python3
"""Simple interactive Redis client for testing."""

import socket

from app.resp import RESPParser, RESPEncoder

def send_command(sock, *args):
    """Send a Redis command and return the parsed response."""
    # Build RESP array
    command = f"*{len(args)}\r\n"
    for arg in args:
        arg_bytes = str(arg).encode('utf-8')
        command += f"${len(arg_bytes)}\r\n{arg}\r\n"
    
    # Send
    sock.sendall(command.encode('utf-8'))
    
    # Receive response
    response_bytes = sock.recv(4096)
    
    # Parse RESP response
    try:
        parsed = RESPParser.parse(response_bytes)
        return parsed, response_bytes
    except Exception as e:
        return f"<Parse Error: {e}>", response_bytes


def format_response(parsed_value):
    """Format the parsed response in a human-friendly way."""
    if parsed_value is None:
        return "(nil)"
    elif isinstance(parsed_value, str):
        return f'"{parsed_value}"'
    elif isinstance(parsed_value, int):
        return f"(integer) {parsed_value}"
    elif isinstance(parsed_value, list):
        result = []
        for i, item in enumerate(parsed_value, 1):
            result.append(f"{i}) {format_response(item)}")
        return "\n".join(result)
    else:
        return str(parsed_value)


def main():
    """Interactive Redis client."""
    # Connect
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('localhost', 6379))
        print("✅ Connected to Redis server on localhost:6379")
        print("Type commands like: PING, ECHO hello, or quit to exit")
        print("Use 'raw' to toggle raw RESP output")
        print("-" * 60)
        
        show_raw = False
        
        while True:
            # Get user input
            try:
                user_input = input("\nredis> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() in ('quit', 'exit'):
                break
            
            if user_input.lower() == 'raw':
                show_raw = not show_raw
                print(f"Raw mode: {'ON' if show_raw else 'OFF'}")
                continue
            
            # Parse command (simple split by spaces, preserving quotes)
            parts = user_input.split()
            
            # Send command
            try:
                parsed, raw_bytes = send_command(sock, *parts)
                
                # Show raw RESP if enabled
                if show_raw:
                    print(f"📦 Raw RESP: {raw_bytes!r}")
                
                # Show parsed response
                if isinstance(parsed, str) and parsed.startswith("<Parse Error"):
                    print(f"❌ {parsed}")
                else:
                    formatted = format_response(parsed)
                    print(formatted)
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    finally:
        sock.close()


if __name__ == "__main__":
    main()

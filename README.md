# Pydis/PyRedis (or Repydis - Redis Implementation in Python)

[![progress-banner](https://backend.codecrafters.io/progress/redis/1d22e86b-0b02-4811-820d-928c2a581686)](https://app.codecrafters.io/users/codecrafters-bot?r=2qF)

A Redis server implementation in Python 3.14+ built for the [CodeCrafters Redis Challenge](https://codecrafters.io/challenges/redis).

This implementation features:
- ✅ **Async I/O** - Handles thousands of concurrent connections using `asyncio`
- ✅ **RESP Protocol** - Full RESP (Redis Serialization Protocol) parser and encoder
- ✅ **Production-Ready** - Clean architecture with separation of concerns
- ✅ **Well-Tested** - Comprehensive test suite with pytest

## 🚀 Quick Start

### Prerequisites

Install [uv](https://github.com/astral-sh/uv) (modern Python package manager):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation

```bash
# Clone the repository (if not already done)
# cd codecrafters-redis-python

# Install dependencies
uv sync

# Or install with dev dependencies (for testing)
uv sync --extra dev
```

### Running the Server

```bash
./run-redis.sh
```

The server will start on `localhost:6379`.


## 🧪 Testing

### Run Test Suite

```bash
# Install all dependencies including dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_resp_parser.py
```

### Interactive Client

Use the built-in interactive client to test your server:

```bash
# Terminal 1: Start server
./run-redis.sh

# Terminal 2: Connect with client
python3 redis_client.py
```

**Client features:**
- Automatic RESP parsing and formatting
- Human-readable output (like `redis-cli`)
- Toggle raw RESP mode with `raw` command
- Syntax: `redis> <command> <args>`

**Example session:**
```
✅ Connected to Redis server on localhost:6379
Type commands like: PING, ECHO hello, or quit to exit
Use 'raw' to toggle raw RESP output
------------------------------------------------------------

redis> PING
"PONG"

redis> ECHO hello world
"hello"

redis> raw
Raw mode: ON

redis> PING
📦 Raw RESP: b'+PONG\r\n'
"PONG"

redis> quit
👋 Goodbye!
```

### Using redis-cli

If you have Redis installed:

```bash
redis-cli -p 6379 PING
redis-cli -p 6379 ECHO "hello world"
```

## 💻 Supported Commands

- ✅ `PING` - Returns PONG
- ✅ `ECHO <message>` - Returns the message
- 🚧 More commands coming soon (SET, GET, etc.)

## 🏗️ Architecture

### Async Server (`app/main.py`)

Uses Python's `asyncio` for efficient I/O multiplexing:
- Single-threaded event loop
- Non-blocking I/O operations
- Handles thousands of concurrent clients
- Graceful connection management

### RESP Protocol (`app/resp/protocol.py`)

Clean, stateless implementation with two classes:

**`RESPParser`**
- Single public method: `parse(data: bytes) -> value`
- Parses RESP wire format into Python objects
- Supports all RESP types: strings, integers, arrays, errors

**`RESPEncoder`**
- Single public method: `encode(value) -> bytes`
- Automatically determines RESP type from Python type
- Clean API: just pass Python values, get RESP bytes

Example:
```python
from app.resp import RESPParser, RESPEncoder

# Parse incoming data
command = RESPParser.parse(b"*2\r\n$4\r\nECHO\r\n$3\r\nhey\r\n")
# → ['ECHO', 'hey']

# Encode responses
response = RESPEncoder.encode("hey")           # → b'$3\r\nhey\r\n'
response = RESPEncoder.encode({'ok': 'PONG'})  # → b'+PONG\r\n'
response = RESPEncoder.encode({'error': 'ERR'}) # → b'-ERR\r\n'
```

## 🔧 Development

### Adding New Commands

1. Add command handler in `app/main.py` → `handle_command()`
2. Add tests in `tests/`
3. Update this README

### Code Style

- **Type hints** where beneficial
- **Docstrings** for public interfaces
- **Private methods** prefixed with `_`
- **Functional approach** - stateless, pure functions where possible

## 📚 Resources

- [RESP Protocol Specification](https://redis.io/docs/reference/protocol-spec/)
- [CodeCrafters Redis Challenge](https://codecrafters.io/challenges/redis)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)

## 📝 License

This is a CodeCrafters challenge project for educational purposes.

---

Built with ❤️ using Python 3.14 and asyncio

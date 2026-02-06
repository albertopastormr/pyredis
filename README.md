# PyRedis - A Redis Implementation in Python

A high-performance Redis server implementation in Python 3.9+ featuring async I/O, full RESP protocol support, and extensive command coverage.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## ✨ Features

- 🚀 **Async I/O** - Built on asyncio for handling thousands of concurrent connections
- 📡 **Full RESP Protocol** - Complete Redis Serialization Protocol (RESP) parser and encoder
- 💾 **Rich Command Set** - Supports strings, lists, streams, transactions, and replication
- 🔄 **Master-Replica Replication** - Full replication support with master-replica synchronization
- 🧪 **Well-Tested** - Comprehensive test suite with unit and integration tests
- 🏗️ **Clean Architecture** - Modular design with clear separation of concerns
- 🎯 **Type-Safe** - Written with type hints throughout

## 📖 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - Deep dive into system design with diagrams
- **[Contributing](CONTRIBUTING.md)** - How to contribute to the project

## 🚀 Quick Start

### Prerequisites

Install [uv](https://github.com/astral-sh/uv) - a fast Python package manager:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation

```bash
# Clone the repository
git clone https://github.com/albertopastormr/pyredis.git
cd pyredis

# Install dependencies
uv sync

# Or install with dev dependencies (for testing)
uv sync --extra dev
```

### Running the Server

```bash
# Start on default port 6379
./run-redis.sh

# Or with custom port
./run-redis.sh --port 6380

# Run as replica
./run-redis.sh --replicaof localhost 6379
```

The server will start and listen for connections.

## 💻 Supported Commands

### Core Commands
- `PING` - Check server connectivity
- `ECHO <message>` - Echo back a message

### String Operations
- `SET key value [EX seconds] [PX milliseconds]` - Set a key with optional expiration
- `GET key` - Get value of a key
- `INCR key` - Increment integer value of a key

### List Operations
- `LPUSH key element [element ...]` - Push elements to the head of a list
- `RPUSH key element [element ...]` - Push elements to the tail of a list
- `LPOP key` - Remove and return the first element
- `LRANGE key start stop` - Get range of elements
- `LLEN key` - Get length of a list
- `BLPOP key [key ...] timeout` - Blocking list pop with timeout

### Stream Operations
- `XADD key ID field value [field value ...]` - Add entry to a stream
- `XRANGE key start end` - Query stream entries by ID range
- `XREAD [BLOCK ms] STREAMS key [key ...] ID [ID ...]` - Read from streams
- `XINFO STREAM key` - Get information about a stream

### Transactions
- `MULTI` - Start a transaction block
- `EXEC` - Execute all commands in transaction
- `DISCARD` - Discard all commands in transaction

### Replication
- `INFO replication` - Get replication information
- `REPLCONF` - Configure replica connection
- `PSYNC` - Synchronize replica with master
- `WAIT numreplicas timeout` - Wait for replicas to acknowledge writes

### Utility
- `TYPE key` - Determine the type of a key

## 🧪 Testing

### Run All Tests

```bash
# Install dev dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/test_resp/test_resp_parser.py

# Run integration tests
uv run pytest tests/integration/
```

### Code Quality

```bash
# Run all quality checks (format, lint, test)
make check

# Format code
make format

# Lint code
make lint

# Run tests
make test
```

## 🔧 Interactive Client

Use the built-in interactive client to test your server:

```bash
# Terminal 1: Start server
./run-redis.sh

# Terminal 2: Connect with client
python3 redis_client.py
```

**Client Features:**
- Automatic RESP parsing and formatting
- Human-readable output (like `redis-cli`)
- Toggle raw RESP mode with `raw` command
- Full command syntax support

**Example Session:**
```
✅ Connected to Redis server on localhost:6379
Type commands like: PING, ECHO hello, or quit to exit
Use 'raw' to toggle raw RESP output
------------------------------------------------------------

redis> PING
"PONG"

redis> SET mykey "Hello World" EX 60
"OK"

redis> GET mykey
"Hello World"

redis> LPUSH mylist item1 item2 item3
3

redis> LRANGE mylist 0 -1
["item3", "item2", "item1"]

redis> quit
👋 Goodbye!
```

### Using redis-cli

You can also use the standard Redis CLI:

```bash
redis-cli -p 6379 PING
redis-cli -p 6379 SET name "Alice"
redis-cli -p 6379 GET name
```

## 🏗️ Architecture

### Project Structure

```
pyredis/
├── app/
│   ├── main.py              # Server entry point and async I/O loop
│   ├── handler.py           # Command handler and dispatcher
│   ├── replica_manager.py   # Replication management
│   ├── commands/            # Command implementations
│   │   ├── base.py         # Abstract base command class
│   │   ├── ping.py         # Individual command modules
│   │   ├── set.py
│   │   └── ...
│   ├── resp/               # RESP protocol implementation
│   │   └── protocol.py     # Parser and encoder
│   └── storage/            # Data storage layer
│       ├── memory.py       # In-memory storage
│       └── streams.py      # Stream data structures
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── run-redis.sh           # Server launcher
├── redis_client.py        # Interactive client
└── pyproject.toml         # Project configuration
```

### Core Components

#### Async Server (`app/main.py`)

Built on Python's `asyncio` for high-performance I/O:
- Single-threaded event loop handles all connections
- Non-blocking I/O operations
- Graceful connection management and cleanup
- Supports thousands of concurrent clients

#### RESP Protocol (`app/resp/protocol.py`)

Clean, stateless implementation with two main classes:

**`RESPParser`**
- Parses RESP wire format into Python objects
- Supports all RESP types: simple strings, bulk strings, integers, arrays, errors
- Efficient byte-level parsing

**`RESPEncoder`**
- Automatically determines RESP type from Python type
- Encodes Python values into RESP wire format
- Clean API: just pass Python values, get RESP bytes

Example:
```python
from app.resp import RESPParser, RESPEncoder

# Parse incoming data
command = RESPParser.parse(b"*2\r\n$4\r\nECHO\r\n$5\r\nhello\r\n")
# → ['ECHO', 'hello']

# Encode responses
response = RESPEncoder.encode("hello")          # → b'$5\r\nhello\r\n'
response = RESPEncoder.encode({'ok': 'PONG'})   # → b'+PONG\r\n'
response = RESPEncoder.encode({'error': 'ERR'})  # → b'-ERR\r\n'
response = RESPEncoder.encode(42)               # → b':42\r\n'
```

#### Command Pattern (`app/commands/`)

Each command is a separate module implementing a common interface:
- Clean separation of concerns
- Easy to add new commands
- Built-in validation and type checking
- Consistent error handling

#### Storage Layer (`app/storage/`)

Pluggable storage backend:
- In-memory storage with TTL support
- Stream data structures with auto-generated IDs
- Type-aware storage (strings, lists, streams)
- Efficient expiration handling

## 🔧 Development

### Adding New Commands

1. Create a new file in `app/commands/your_command.py`:
```python
from app.commands.base import Command

class YourCommand(Command):
    """Description of your command"""
    
    @property
    def name(self) -> str:
        return "YOURCOMMAND"
    
    def execute(self, storage, *args):
        # Implementation here
        return result
```

2. Register in `app/commands/__init__.py`
3. Add tests in `tests/unit/test_your_command.py`
4. Update this README


### Running Quality Checks

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type check (if you add mypy)
uv run mypy app/

# Run all checks at once
make check
```

## 📚 Resources

- [Redis Documentation](https://redis.io/docs/)
- [RESP Protocol Specification](https://redis.io/docs/reference/protocol-spec/)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Redis Commands Reference](https://redis.io/commands/)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the Redis project and its excellent documentation
- Built with modern Python tooling (uv, ruff, pytest)

---

⭐ **Built with ❤️ using Python and asyncio** ⭐

# Architecture Overview

This document provides a deep dive into PyRedis's architecture, design decisions, and internal workings.

## 📐 High-Level Architecture

```mermaid
graph TB
    Client[Redis Client] -->|TCP Connection| Server[Async Server]
    Server -->|Parse RESP| Parser[RESP Parser]
    Parser -->|Command Array| Handler[Command Handler]
    Handler -->|Dispatch| Registry[Command Registry]
    Registry -->|Execute| Commands[Command Implementations]
    Commands -->|Read/Write| Storage[Storage Layer]
    Commands -->|Encode| Encoder[RESP Encoder]
    Encoder -->|Response| Client
    
    Handler -->|Transaction?| TxnMgr[Transaction Manager]
    TxnMgr -->|Queue/Execute| Commands
    
    Handler -->|Write Command?| RepMgr[Replica Manager]
    RepMgr -->|Propagate| Replicas[Connected Replicas]
    
    style Server fill:#e1f5ff
    style Storage fill:#fff4e1
    style Commands fill:#f0e1ff
    style RepMgr fill:#e1ffe1
```

## 🔄 Request Flow

### 1. Client Connection & Command Processing

```mermaid
sequenceDiagram
    participant Client
    participant Server
    participant Parser as RESP Parser
    participant Handler
    participant Command
    participant Storage
    participant Encoder as RESP Encoder
    
    Client->>Server: TCP Connection
    Client->>Server: Send RESP data
    Server->>Parser: parse(bytes)
    Parser->>Parser: Identify RESP types
    Parser-->>Handler: Return parsed array
    Handler->>Command: execute(args)
    Command->>Storage: get/set/xadd/etc
    Storage-->>Command: Result
    Command-->>Handler: Response
    Handler->>Encoder: encode(response)
    Encoder-->>Client: RESP bytes
```

### 2. Master-Replica Replication Flow

```mermaid
sequenceDiagram
    participant Replica
    participant Master
    participant RepMgr as Replica Manager
    participant Storage
    
    Note over Replica,Master: Handshake Phase
    Replica->>Master: PING
    Master-->>Replica: +PONG
    Replica->>Master: REPLCONF listening-port 6380
    Master-->>Replica: +OK
    Replica->>Master: REPLCONF capa psync2
    Master-->>Replica: +OK
    Replica->>Master: PSYNC ? -1
    Master->>RepMgr: Register replica
    Master-->>Replica: +FULLRESYNC <replid> 0
    Master-->>Replica: RDB file (empty)
    
    Note over Replica,Master: Propagation Phase
    loop On each write command
        Master->>Storage: Execute write (SET, LPUSH, etc)
        Master->>RepMgr: Propagate command
        RepMgr->>Replica: Forward command (RESP)
        Replica->>Replica: Execute command silently
    end
```

### 3. Transaction Execution (MULTI/EXEC)

```mermaid
stateDiagram-v2
    [*] --> Normal: Client connects
    Normal --> InTransaction: MULTI command
    InTransaction --> InTransaction: Queue commands
    InTransaction --> Normal: EXEC (execute all)
    InTransaction --> Normal: DISCARD (drop all)
    Normal --> [*]: Client disconnects
    
    note right of InTransaction
        Commands are queued,
        not executed immediately.
        Each returns "QUEUED"
    end note
    
    note right of Normal
        Commands execute
        immediately and
        return results
    end note
```

### 4. Streams with Blocking Reads (XREAD BLOCK)

```mermaid
sequenceDiagram
    participant Client1 as Client 1 (XREAD)
    participant Client2 as Client 2 (XADD)
    participant Server
    participant BlockMgr as Blocking Manager
    participant Storage
    
    Client1->>Server: XREAD BLOCK 1000 STREAMS mystream $
    Server->>BlockMgr: Register blocking read
    Note over Client1,BlockMgr: Client 1 waits...
    
    Client2->>Server: XADD mystream * field value
    Server->>Storage: Add entry to stream
    Storage-->>Server: Entry ID
    Server->>BlockMgr: notify_key("mystream")
    BlockMgr->>Client1: Wake up reader
    Server->>Storage: Read new entries
    Storage-->>Client1: Return entries
    
    Server-->>Client2: Return entry ID
```

## 🏗️ Core Components

### RESP Protocol Layer

The RESP (Redis Serialization Protocol) implementation is the foundation:

```python
# Parser: Bytes → Python Objects
RESPParser.parse(b"*2\r\n$4\r\nECHO\r\n$5\r\nhello\r\n")
# → ['ECHO', 'hello']

# Encoder: Python Objects → Bytes
RESPEncoder.encode("hello")  # → b'$5\r\nhello\r\n'
RESPEncoder.encode(42)       # → b':42\r\n'
RESPEncoder.encode(None)     # → b'$-1\r\n'
```

**Key Design Decisions:**
- **Stateless**: Each parse/encode is independent
- **Recursive**: Handles nested arrays naturally
- **Type mapping**: Automatic Python ↔ RESP type conversion

### Command Registry Pattern

Commands are self-registering through metaclass magic:

```mermaid
classDiagram
    class Command {
        <<abstract>>
        +name() str
        +execute(args) Any
        +is_write_command bool
        +bypasses_transaction_queue bool
    }
    
    class CommandRegistry {
        -_commands: dict
        +register(cmd_class)
        +get(name) Command
    }
    
    class SetCommand {
        +name() "SET"
        +is_write_command True
        +execute(args)
    }
    
    class GetCommand {
        +name() "GET"
        +is_write_command False
        +execute(args)
    }
    
    Command <|-- SetCommand
    Command <|-- GetCommand
    CommandRegistry --> Command : manages
```

Benefits:
- **Easy to extend**: Add new command = create new file
- **Type safe**: Base class enforces interface
- **Testable**: Each command is isolated

### Storage Layer

```mermaid
graph LR
    A[Storage Interface] --> B[String Storage]
    A --> C[List Storage]
    A --> D[Stream Storage]
    
    B --> E[TTL Manager]
    C --> E
    D --> E
    
    E --> F[In-Memory HashMap]
    
    style A fill:#e1f5ff
    style E fill:#fff4e1
    style F fill:#f0e1ff
```

**Features:**
- **Type-aware**: Different operations for strings, lists, streams
- **TTL support**: Automatic expiration using timestamps
- **Stream IDs**: Auto-generation with millisecond precision

### Async I/O Architecture

```python
# Single event loop handles all connections
async def main():
    server = await asyncio.start_server(
        handle_client,
        host="localhost",
        port=6379
    )
    async with server:
        await server.serve_forever()

# Each client gets a coroutine
async def handle_client(reader, writer):
    while True:
        data = await reader.read(1024)  # Non-blocking
        response = await execute_command(...)  # May block internally
        writer.write(response)
        await writer.drain()  # Non-blocking
```

**Why asyncio?**
- ✅ Single thread handles thousands of connections
- ✅ No race conditions (cooperative multitasking)
- ✅ Perfect for I/O-bound workloads like Redis
- ✅ Built-in timeout and cancellation support

## 📊 Data Structures

### Stream Entry Storage

Streams are the most complex data structure:

```python
{
    "mystream": StreamData(
        entries=[
            StreamEntry(
                id="1234567890-0",
                fields={"temperature": "20", "humidity": "65"}
            ),
            StreamEntry(
                id="1234567890-1", 
                fields={"temperature": "21", "humidity": "64"}
            )
        ],
        last_id="1234567890-1"
    )
}
```

**ID Format:** `<milliseconds>-<sequence>`
- Monotonically increasing
- Supports range queries
- Enables auto-generation

### Blocking Operations

```python
# Blocking registry maps keys to waiting clients
{
    "mystream": [
        BlockingRead(
            reader=<StreamReader>,
            writer=<StreamWriter>,
            timeout=asyncio.create_task(...),
            trigger_count=1
        )
    ]
}
```

When `XADD` occurs:
1. Add entry to storage
2. Check blocking registry
3. Wake up waiting readers
4. Cancel their timeout tasks

## 🔐 Security Considerations

Currently implemented:
- ✅ Input validation (command arguments)
- ✅ RESP protocol validation
- ✅ Type checking for all operations

**Not yet implemented:**
- ❌ Authentication (ACL)
- ❌ TLS/SSL encryption
- ❌ Resource limits (max connections, memory)

## 🚀 Performance Characteristics

| Operation | Time Complexity | Notes |
|-----------|----------------|-------|
| `SET` | O(1) | Hash table insert |
| `GET` | O(1) | Hash table lookup |
| `LPUSH/RPUSH` | O(1) | Deque append |
| `LRANGE` | O(S+N) | S: start offset, N: range size |
| `XADD` | O(1) | Append + ID generation |
| `XRANGE` | O(N) | N: matching entries |
| `XREAD BLOCK` | O(1) | Registration, O(N) on wake |

**Memory:**
- All data in-memory (no disk persistence yet)
- TTL cleanup on access (lazy eviction)
- No memory limits enforced


## 📚 Learning Resources

This implementation demonstrates:

1. **Protocol Design**: How Redis's RESP protocol enables efficient client-server communication
2. **Async I/O**: Using Python's asyncio for high-concurrency network services
3. **Distributed Systems**: Master-replica replication, eventual consistency
4. **Data Structures**: Efficient in-memory storage with TTL
5. **Command Pattern**: Extensible architecture for adding features
6. **Testing**: Unit and integration testing for complex systems

## 🤝 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details on:
- Adding new commands
- Improving performance
- Extending storage layer
- Adding new data types

---

**Built with ❤️ to teach Redis internals and async Python**

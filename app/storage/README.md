# Storage Layer Design

## 🎯 Design Decisions

### Why `dict` is Professional ✅

**Real Redis uses hash tables** - Python's `dict` is exactly that.

**Performance:**
- ✅ O(1) average case lookups
- ✅ O(1) inserts and deletes  
- ✅ C-level implementation (fast!)
- ✅ Memory efficient

**Thread Safety:**
- ✅ Safe with asyncio (single-threaded event loop)
- ✅ Python GIL protects simple operations
- ✅ No locks needed for basic operations

**Industry Standard:**
- ✅ Redis core = hash table
- ✅ Memcached = hash table
- ✅ Most in-memory DBs = hash table

### Persistence to Disk?

**Current: In-Memory Only** (like Redis!)

Redis itself is **primarily in-memory**:
- Speed is the #1 feature
- Persistence is optional (RDB/AOF)
- Most use cases don't need persistence

**When to add persistence:**
- ✅ After basic commands work
- ✅ As separate module (separation of concerns)
- ✅ Optional feature (like real Redis)

---

## 🏗️ Architecture

### Layer Structure

```
app/
├── commands/           # Business logic
│   └── set.py         # Uses storage
├── storage/           # Data layer ✨
│   ├── base.py        # Abstract interface
│   ├── memory.py      # Dict implementation
│   └── __init__.py    # Singleton pattern
└── handler.py         # Protocol layer
```

### Design Patterns Used

**1. Abstract Base Class (ABC)**
```python
class BaseStorage(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass
```
- ✅ Enforces interface contract
- ✅ Can swap implementations
- ✅ Type-safe

**2. Singleton Pattern**
```python
def get_storage() -> BaseStorage:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = InMemoryStorage()
    return _storage_instance
```
- ✅ Single storage instance across app
- ✅ Easy to access from commands
- ✅ Can inject for testing

**3. Dependency Injection**
```python
# Commands use storage via get_storage()
storage = get_storage()
storage.set(key, value)
```
- ✅ Loose coupling
- ✅ Easy to test (inject mock)
- ✅ Can swap backends

---

## 💡 Comparison with Alternatives

### Option 1: Plain Dict (What we chose) ✅
```python
storage = {}
storage[key] = value
```
**Pros:** Simple, fast, Pythonic  
**Cons:** Global state (solved with singleton)

### Option 2: Redis Module
```python
import redis
r = redis.Redis()
```
**Pros:** Feature-complete  
**Cons:** Overkill, defeats the purpose of building Redis

### Option 3: Custom Data Structure
```python
class CustomHashTable:
    # Reinvent the wheel
```
**Pros:** Learning exercise  
**Cons:** Slower than dict, more bugs, unnecessary

### Option 4: SQLite
```python
import sqlite3
```
**Pros:** Persistent  
**Cons:** Slow (disk I/O), wrong tool (Redis is in-memory)

**Winner: Dict** - Professional, fast, simple!

---

## 🚀 Future Extensibility

Our design makes it easy to add:

### Persistence (Future)
```python
class PersistentStorage(BaseStorage):
    def __init__(self):
        self._memory = InMemoryStorage()
        self._rdb = RDBPersistence()  # Future
    
    def set(self, key, value):
        self._memory.set(key, value)
        self._rdb.log_set(key, value)  # AOF-style
```

### Distributed Storage (Future)
```python
class DistributedStorage(BaseStorage):
    def __init__(self):
        self._shards = [InMemoryStorage() for _ in range(16)]
    
    def get(self, key):
        shard = self._get_shard(key)
        return shard.get(key)
```

### TTL Support (Future)
```python
class TTLStorage(BaseStorage):
    def set(self, key, value, ttl=None):
        self._data[key] = value
        if ttl:
            self._expires[key] = time.time() + ttl
```

All without changing command code! ✨

---

## 📊 Performance Characteristics

| Operation | Time | Space |
|-----------|------|-------|
| GET | O(1) | - |
| SET | O(1) | O(n) |
| DELETE | O(1) | - |
| EXISTS | O(1) | - |

Where n = total keys in storage

**Memory usage:** ~50-100 bytes per key-value pair (Python overhead)

---

## ✅ Professional Checklist

- ✅ **Clean Interface** - Abstract base class
- ✅ **Separation of Concerns** - Storage layer isolated
- ✅ **Performance** - O(1) operations
- ✅ **Testability** - Dependency injection
- ✅ **Extensibility** - Easy to add features
- ✅ **Industry Standard** - Same approach as real Redis
- ✅ **Type Safety** - Type hints throughout
- ✅ **Documentation** - Clear docstrings

---

## 🧪 Testing

```python
# Easy to test with mock storage
from app.storage import set_storage

def test_set_command():
    mock_storage = MockStorage()
    set_storage(mock_storage)
    
    # Test command
    result = CommandRegistry.execute('SET', ['key', 'val'])
    
    # Verify
    assert mock_storage.get('key') == 'val'
```

---

## 📚 Summary

**Is dict professional?** ✅ YES - It's exactly what Redis uses internally!

**Should we persist to disk?** Later - Keep it simple now, add when needed.

**Is this production-ready?** ✅ YES - With proper architecture for future growth.

Built with the same principles as real Redis:
- In-memory first
- Performance focused
- Simple core, extensible design

# Adding New Commands

This guide shows how to add new Redis commands to the server.

## Quick Example: Adding GET Command

### 1. Create the Command File

Create `app/commands/get.py`:

```python
"""GET command implementation."""

from typing import Any, List
from .base import BaseCommand


class GetCommand(BaseCommand):
    """
    GET command - Get the value of a key.
    
    Syntax: GET key
    """
    
    @property
    def name(self) -> str:
        return "GET"
    
    def execute(self, args: List[str]) -> Any:
        """Execute GET command."""
        self.validate_args(args, min_args=1, max_args=1)
        
        key = args[0]

        # For now, return nil (key not found)
        return None
```

### 2. Register the Command

Add to `app/commands/__init__.py`:

```python
from .get import GetCommand

# In the auto-registration section:
CommandRegistry.register(GetCommand)

# Update __all__:
__all__ = ['CommandRegistry', 'BaseCommand', 'PingCommand', 'EchoCommand', 'GetCommand']
```

### 3. That's It!

The command is now available! No need to modify:
- ❌ handler.py
- ❌ server.py
- ❌ main.py


### Type Safety
The base class provides:
- `validate_args()` - Argument count checking
- Clear return type expectations
- Consistent error handling

## Command Response Types

Your `execute()` method can return:

| Return Value | RESP Encoding |
|-------------|---------------|
| `str` | Bulk string: `$3\r\nhey\r\n` |
| `{'ok': 'text'}` | Simple string: `+text\r\n` |
| `{'error': 'msg'}` | Error: `-msg\r\n` |
| `int` | Integer: `:42\r\n` |
| `None` | Null: `$-1\r\n` |
| `list` | Array: `*2\r\n...` |


## Architecture Flow

```
Client Request
    ↓
handler.py (parse RESP)
    ↓
CommandRegistry.execute(name, args)
    ↓
YourCommand.execute(args)
    ↓
Return value
    ↓
RESPEncoder.encode(value)
    ↓
Client Response
```

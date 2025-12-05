"""
RESP Module API Documentation
==============================

This module provides a clean, simple API for working with Redis RESP protocol.

Classes:
--------
1. RESPParser - Parse RESP bytes into Python values
2. RESPEncoder - Encode Python values into RESP bytes


PUBLIC API (use these):
-----------------------

RESPParser.parse(data: bytes) -> Python value
    Parse RESP protocol bytes and return Python objects.
    
    Examples:
        >>> RESPParser.parse(b"*2\r\n$4\r\nECHO\r\n$3\r\nhey\r\n")
        ['ECHO', 'hey']
        
        >>> RESPParser.parse(b"+OK\r\n")
        'OK'


RESPEncoder.encode(value) -> bytes
    Encode a Python value to RESP protocol bytes.
    Automatically determines the correct RESP type.
    
    Supported types:
    - str         → Bulk String: $3\r\nhey\r\n
    - int         → Integer: :42\r\n
    - list        → Array: *2\r\n$3\r\nhey\r\n...
    - None        → Null: $-1\r\n
    - {'ok': x}   → Simple String: +OK\r\n
    - {'error': x} → Error: -ERR message\r\n
    
    Examples:
        >>> RESPEncoder.encode("hey")
        b'$3\r\nhey\r\n'
        
        >>> RESPEncoder.encode({'ok': 'PONG'})
        b'+PONG\r\n'
        
        >>> RESPEncoder.encode({'error': 'ERR unknown command'})
        b'-ERR unknown command\r\n'
        
        >>> RESPEncoder.encode(['SET', 'key', 'value'])
        b'*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n'


USAGE IN YOUR CODE:
-------------------

from app.resp import RESPParser, RESPEncoder

# Parse incoming data
command = RESPParser.parse(data)

# Encode responses
response = RESPEncoder.encode({'ok': 'PONG'})
response = RESPEncoder.encode("hello")
response = RESPEncoder.encode({'error': 'ERR something went wrong'})


DESIGN PRINCIPLES:
------------------
✅ Separated classes for parsing vs encoding (Single Responsibility)
✅ Single public method per class (Simple API)
✅ All implementation details are private (Good encapsulation)
✅ Stateless/functional design (Thread-safe, predictable)
✅ Type-based automatic encoding (No need to know RESP types)
"""

# Test Structure Guide

This document explains our reorganized test structure separating unit and integration tests.

## 📁 New Test Structure

```
tests/
├── unit/                       # Test components in isolation
│   ├── test_commands/          # Individual command tests
│   │   ├── test_ping.py
│   │   └── test_echo.py
│   ├── test_get.py             # GET command tests
│   ├── test_set.py             # SET command tests
│   ├── test_handler.py         # Handler logic tests
│   └── test_resp/              # RESP protocol tests
│       └── test_resp_parser.py
│
├── integration/                # Test complete workflows
│   ├── test_basic_commands.py  # PING/ECHO integration
│   ├── test_storage_commands.py # SET/GET integration
│   └── test_error_handling.py  # Error handling flows
│
├── conftest.py                 # Shared pytest fixtures
└── README.md                   # This file
```

## 🎯 Unit vs Integration Tests

### Unit Tests (`tests/unit/`)
**Purpose:** Test individual components in isolation

**Characteristics:**
- ✅ Fast (no cross-layer dependencies)
- ✅ Focused (one component at a time)
- ✅ Mock/isolate dependencies
- ✅ Easy to debug

**Examples:**
```python
# Test SET command alone
def test_set_simple_value():
    cmd = SetCommand()
    result = cmd.execute(['key', 'value'])
    assert result == {'ok': 'OK'}
```

### Integration Tests (`tests/integration/`)
**Purpose:** Test complete workflows across layers

**Characteristics:**
- ✅ Test real interactions
- ✅ Verify layer integration
- ✅ End-to-end scenarios
- ✅ Catch interface issues

**Examples:**
```python
# Test full SET → GET flow
def test_set_then_get():
    # Parse RESP → Execute → Encode response
    set_request = b"*3\r\n$3\r\nSET\r\n..."
    # ... verify end-to-end
```

## ✅ Current Test Coverage

### Unit Tests: 60 tests
- **Commands** (30 tests)
  - PING: 5 tests
  - ECHO: 7 tests
  - SET: 9 tests
  - GET: 9 tests
- **Handler** (7 tests)
- **RESP Protocol** (23 tests)

### Integration Tests: 14 tests
- **Basic Commands** (4 tests) - PING/ECHO flows
- **Storage Commands** (5 tests) - SET/GET flows
- **Error Handling** (5 tests) - Error scenarios

**Total: 74 tests, all passing** ✅

## 🚀 Running Tests

### Run All Tests
```bash
pytest
```

### Run Only Unit Tests
```bash
pytest tests/unit/
```

### Run Only Integration Tests
```bash
pytest tests/integration/
```

### Run Specific Test File
```bash
pytest tests/unit/test_set.py
```

### Run With Coverage
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### Run Verbose
```bash
pytest -v
```

### Run and Stop on First Failure
```bash
pytest -x
```

## 📝 Adding New Tests

### Adding Unit Test for New Command

**1. Create test file:**
```bash
tests/unit/test_mycommand.py
```

**2. Write tests:**
```python
"""Tests for MYCOMMAND."""

import pytest
from app.commands.mycommand import MyCommand

class TestMyCommand:
    def test_basic_functionality(self):
        cmd = MyCommand()
        result = cmd.execute(['arg'])
        assert result == expected
```

### Adding Integration Test

**1. Add to appropriate file:**
- Basic commands → `test_basic_commands.py`
- Storage ops → `test_storage_commands.py`
- Errors → `test_error_handling.py`
- New category → Create new file

**2. Write test:**
```python
def test_my_workflow():
    # Build RESP request
    request = RESPEncoder.encode([...])
    
    # Parse → Execute → Encode
    command = RESPParser.parse(request)
    result = execute_command(command)
    response = RESPEncoder.encode(result)
    
    # Verify
    assert response == expected
```

## 🎨 Test Principles

### 1. Isolation (Unit Tests)
- No shared state between tests
- Use `setup_method()` for cleanup
- Mock external dependencies

### 2. Realistic (Integration Tests)
- Test actual component interactions
- Use real storage (but reset it)
- Verify full request/response cycle

### 3. Clear Names
```python
# Good ✅
def test_set_overwrites_existing_key():
    ...

# Bad ❌
def test_set2():
    ...
```

### 4. One Assertion Per Concept
```python
# Good ✅
def test_set_stores_value():
    cmd.execute(['key', 'value'])
    assert storage.get('key') == 'value'

def test_set_returns_ok():
    result = cmd.execute(['key', 'value'])
    assert result == {'ok': 'OK'}
```

### 5. Test Edge Cases
- Empty values
- Special characters
- Boundary conditions
- Error cases

## 📊 Test Organization Benefits

### Clear Separation
- Know where to add tests
- Easy to run subset of tests
- Faster feedback loop

### Better Debugging
- Unit test fails? Issue in component
- Integration test fails? Issue in integration

### Scalability
- Easy to add new test categories
- Tests don't get cluttered
- Maintainable structure

## 🔧 Fixtures

Common fixtures in `conftest.py`:
- `event_loop` - For async tests
- `unused_tcp_port` - For server tests

Command-specific fixtures in test files:
```python
@pytest.fixture
def storage():
    """Clean storage for each test."""
    reset_storage()
    return get_storage()
```

## 📈 Coverage Goals

- **Commands**: 100% (critical business logic)
- **Storage**: 95%+ (data integrity)
- **Handler**: 90%+ (protocol handling)
- **RESP**: 100% (protocol correctness)
- **Integration**: Key user flows

## 🎯 Test Hierarchy

```
Unit Tests (Fast, Focused)
    ↓
Integration Tests (Realistic, Comprehensive)
    ↓
Manual Testing (redis_client.py)
    ↓
Production (Real users)
```

---

**Keep tests clean, organized, and comprehensive!** 🚀

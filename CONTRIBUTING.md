# Contributing to PyRedis

Thank you for considering contributing to PyRedis! This document provides guidelines and instructions for contributing.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Development Setup

1. **Fork and clone the repository**
```bash
git clone https://github.com/albertopastormr/pyredis.git
cd pyredis
```

2. **Install dependencies**
```bash
uv sync --extra dev
```

3. **Verify setup**
```bash
make check
```

## 🔧 Development Workflow

### Before Making Changes

1. Create a new branch for your feature or bugfix:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bugfix-name
```

2. Make sure all tests pass:
```bash
uv run pytest
```

### Making Changes

#### Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for formatting and linting:

```bash
# Format your code
uv run ruff format .

# Check for lint errors
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check . --fix
```

#### Type Hints

- Use type hints for all function parameters and return values
- Keep type hints clean and readable

#### Documentation

- Add docstrings to all public classes, methods, and functions
- Use Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """Short description of the function.
    
    Longer description if needed, explaining what the function does
    in more detail.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something is invalid
    """
    pass
```

### Adding New Commands

1. **Create command file** in `app/commands/your_command.py`:

```python
from app.commands.base import Command

class YourCommand(Command):
    """Implementation of the YOUR_COMMAND Redis command.
    
    YOUR_COMMAND does something useful.
    
    Syntax: YOUR_COMMAND arg1 [arg2]
    
    Returns:
        Description of what it returns
    """
    
    @property
    def name(self) -> str:
        return "YOUR_COMMAND"
    
    def execute(self, storage, *args):
        """Execute the YOUR_COMMAND command.
        
        Args:
            storage: Storage instance
            *args: Command arguments
            
        Returns:
            Command result
        """
        # Validate arguments
        if len(args) < 1:
            return {"error": "ERR wrong number of arguments"}
        
        # Implementation
        result = do_something(args)
        return result
```

2. **Register the command** in `app/commands/__init__.py`:

```python
from app.commands.your_command import YourCommand

# Add to __all__
__all__ = [
    # ... existing commands
    "YourCommand",
]
```

3. **Add tests** in `tests/unit/test_your_command.py`:

```python
import pytest
from app.commands.your_command import YourCommand
from app.storage.memory import InMemoryStorage

def test_your_command_basic():
    """Test basic functionality of YOUR_COMMAND."""
    storage = InMemoryStorage()
    cmd = YourCommand()
    
    result = cmd.execute(storage, "arg1", "arg2")
    
    assert result == expected_value

def test_your_command_error_handling():
    """Test error handling in YOUR_COMMAND."""
    storage = InMemoryStorage()
    cmd = YourCommand()
    
    result = cmd.execute(storage)  # Missing arguments
    
    assert "error" in result
```

4. **Add integration tests** if needed in `tests/integration/`

5. **Update documentation** in README.md

### Testing

#### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_your_command.py

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run integration tests only
uv run pytest tests/integration/
```

#### Writing Good Tests

- Test both success and error cases
- Use descriptive test names: `test_<what>_<when>_<expected>`
- Keep tests focused and independent
- Use fixtures for common setup
- Aim for high code coverage (>80%)

### Quality Checks

Before committing, run all quality checks:

```bash
make check
```

This will:
1. Format code with Ruff
2. Lint code with Ruff
3. Run all tests

## 📝 Commit Guidelines

### Commit Messages

Write clear, descriptive commit messages:

```
Add LPUSH command implementation

- Implement LPUSH for adding elements to list head
- Add unit tests for various scenarios
- Update README with command documentation
```

Format:
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed description with bullet points

### Commit Best Practices

- Make atomic commits (one logical change per commit)
- Test before committing
- Don't commit generated files or dependencies
- Keep commits focused and small

## 🔄 Pull Request Process

1. **Update your branch** with the latest changes from main:
```bash
git checkout main
git pull origin main
git checkout your-branch
git rebase main
```

2. **Ensure all checks pass**:
```bash
make check
```

3. **Push your changes**:
```bash
git push origin your-branch
```

4. **Create a Pull Request** on GitHub:
   - Use a clear, descriptive title
   - Describe what changes you made and why
   - Reference any related issues
   - Request review from maintainers

5. **Address review feedback**:
   - Make requested changes
   - Push updates to your branch
   - Respond to comments

6. **Merge**: Once approved, a maintainer will merge your PR

## 🐛 Reporting Bugs

### Before Reporting

- Check if the bug has already been reported
- Verify the bug exists in the latest version
- Collect information about your environment

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. See error

**Expected behavior**
What you expected to happen.

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11]
- PyRedis version: [e.g., 1.0.0]

**Additional context**
Any other relevant information.
```

## 💡 Suggesting Enhancements

We welcome enhancement suggestions! Please:

1. Check if the enhancement has already been suggested
2. Clearly describe the enhancement and its benefits
3. Provide examples of how it would be used
4. Explain why this enhancement would be useful

## 📋 Development Tasks

### Adding a New Data Type

1. Create storage class in `app/storage/`
2. Implement commands in `app/commands/`
3. Add comprehensive tests
4. Update documentation

### Improving Performance

1. Profile the code to identify bottlenecks
2. Implement optimizations
3. Add benchmarks to verify improvements
4. Document performance improvements

### Adding Features

1. Discuss the feature in an issue first
2. Follow the development workflow above
3. Ensure backward compatibility
4. Update all relevant documentation

## ❓ Questions?

If you have questions:
- Open an issue for discussion
- Check existing issues and documentation
- Reach out to maintainers

## 🙏 Thank You!

Your contributions make PyRedis better for everyone. We appreciate your time and effort!

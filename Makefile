# Makefile for running all quality checks with a single command
# Usage: make check

.PHONY: help check format lint test clean install

export PATH := $(HOME)/.local/bin:$(PATH)

help:
	@echo "Available commands:"
	@echo "  make check    - Run all checks (format, lint, test)"
	@echo "  make format   - Format code with ruff"
	@echo "  make lint     - Lint code with ruff"
	@echo "  make test     - Run tests with pytest"
	@echo "  make install  - Install dev dependencies with uv"
	@echo "  make clean    - Clean up cache files"

check: format lint test
	@echo "✅ All checks passed!"

format:
	@echo "🎨 Formatting code..."
	@uv run ruff format .

lint:
	@echo "🔍 Linting code..."
	@uv run ruff check . --fix

test:
	@echo "🧪 Running tests..."
	@uv run pytest

install:
	@echo "📦 Installing dependencies with uv..."
	@uv pip install ruff pytest

clean:
	@echo "🧹 Cleaning cache..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete

"""Shared fixtures for integration tests."""

import pytest

from app.storage import get_storage


@pytest.fixture(autouse=True)
def clean_storage():
    """Reset storage before each test."""
    storage = get_storage()
    storage.clear()
    yield
    storage.clear()

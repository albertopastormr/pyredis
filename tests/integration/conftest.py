"""Shared fixtures for integration tests."""

import pytest
from app.storage import reset_storage


@pytest.fixture(autouse=True)
def clean_storage():
    """
    Automatically reset storage before each integration test.
    
    This fixture runs before every test in the integration directory,
    ensuring tests don't interfere with each other.
    """
    reset_storage()
    yield
    # Optional: cleanup after test if needed

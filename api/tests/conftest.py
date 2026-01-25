"""Pytest configuration and fixtures for API tests."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create test client for API tests."""
    return TestClient(app)

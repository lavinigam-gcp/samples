"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import shutil

from ucp_store_mocker.config.schema import StoreConfig
from ucp_store_mocker.config.defaults import get_store_defaults


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def grocery_config():
    """Create a grocery store configuration."""
    defaults = get_store_defaults("grocery", "Test Grocery")
    return StoreConfig(**defaults)


@pytest.fixture
def electronics_config():
    """Create an electronics store configuration."""
    defaults = get_store_defaults("electronics", "Test Electronics")
    return StoreConfig(**defaults)


@pytest.fixture
def minimal_config():
    """Create a minimal store configuration."""
    return StoreConfig(
        store={"name": "Minimal Store", "type": "grocery"},
        server={"port": 8080},
    )


@pytest.fixture
def sample_products():
    """Sample product data for testing."""
    return [
        {"id": "prod-001", "title": "Test Product 1", "category": "Test", "price": 999},
        {"id": "prod-002", "title": "Test Product 2", "category": "Test", "price": 1999},
        {"id": "prod-003", "title": "Test Product 3", "category": "Other", "price": 2999},
    ]

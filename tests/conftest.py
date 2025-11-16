"""
Pytest configuration and fixtures
"""

import pytest
import tempfile
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, 'test_memory.db')


@pytest.fixture
def mock_request():
    """Create a mock Flask request object"""
    class MockRequest:
        def __init__(self):
            self.headers = {}
            self.args = {}

    return MockRequest()


@pytest.fixture
def sample_text():
    """Sample text for testing"""
    return "Hello World! This is a test string with emails like test@example.com and URLs like https://example.com/page"


@pytest.fixture
def sample_json():
    """Sample JSON for testing"""
    return '{"name": "test", "value": 123, "active": true}'


@pytest.fixture
def invalid_json():
    """Invalid JSON for testing"""
    return '{"name": "test", value: 123}'

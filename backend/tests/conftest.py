"""
Pytest configuration and shared fixtures for Spica backend tests.
"""

import pytest
import asyncio


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for each test function."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def anyio_backend():
    """Use asyncio as the async backend."""
    return "asyncio"

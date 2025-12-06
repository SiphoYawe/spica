"""
Tests for main FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns correct response"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Spica API"
    assert "version" in data


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    # Legacy endpoint just returns status, message, and timestamp
    assert "message" in data
    assert "timestamp" in data

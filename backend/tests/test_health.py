"""Unit tests for GridMind AI initial endpoints."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_health():
    """Verify /health returns HTTP 200 with ok status and required fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data


def test_get_root():
    """Verify / returns application name, description, and docs link."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "GridMind AI"
    assert "solar" in data["description"].lower() or "energy" in data["description"].lower()
    assert data["docs_url"] == "/docs"


def test_cors_preflight():
    """Verify CORS preflight headers for frontend origin."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"

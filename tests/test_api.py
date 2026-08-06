import pytest
from fastapi.testclient import TestClient

from src.api import app


@pytest.fixture
def client() -> TestClient:
    """Create TestClient instance."""
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_stats(client: TestClient) -> None:
    """Test stats endpoint."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "processed" in data
    assert "failed" in data
    assert "success_rate" in data


def test_process_transaction(client: TestClient) -> None:
    """Test transaction processing endpoint."""
    payload = {
        "id": "tx_api_001",
        "tenant_id": "tenant_api",
        "amount": "100.50",
        "region": "EU",
        "timestamp": "2026-08-14T12:00:00+00:00",
    }
    response = client.post("/process", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "processed" in data
    assert "failed" in data
    assert "success_rate" in data


def test_get_metrics(client: TestClient) -> None:
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "settlement_transactions_processed_total" in response.text

"""API endpoint tests."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.api import app, orchestrator
from src.auth import jwt_auth, JWTAuthenticator


@pytest.fixture
def client() -> TestClient:
    """Create TestClient instance."""
    return TestClient(app)


@pytest.fixture
def valid_token() -> str:
    """Create valid JWT token for testing."""
    return jwt_auth.create_token(
        user_id="test_user",
        tenant_id="test_tenant",
        scopes=["read", "write"],
    )


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint (no auth required)."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "settlement-pipeline"


def test_login_success(client: TestClient) -> None:
    """Test successful login."""
    response = client.post(
        "/auth/login",
        json={
            "username": "test_user",
            "password": "test_password",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 3600


def test_login_failure(client: TestClient) -> None:
    """Test failed login with empty password."""
    response = client.post(
        "/auth/login",
        json={
            "username": "test_user",
            "password": "",
        },
    )

    assert response.status_code == 401
    data = response.json()
    assert "Invalid credentials" in data["detail"]


def test_get_stats_no_auth(client: TestClient) -> None:
    """Test stats endpoint without auth returns 401."""
    response = client.get("/stats")

    assert response.status_code == 401


def test_get_stats_with_auth(
    client: TestClient,
    valid_token: str,
) -> None:
    """Test stats endpoint with valid JWT token."""
    with patch.object(
        orchestrator,
        "get_stats",
        return_value={"processed": 100, "failed": 0},
    ):
        response = client.get(
            "/stats",
            headers={"Authorization": f"Bearer {valid_token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["processed"] == 100
    assert data["failed"] == 0


def test_get_stats_invalid_token(client: TestClient) -> None:
    """Test stats endpoint with invalid token."""
    response = client.get(
        "/stats",
        headers={"Authorization": "Bearer invalid.token.here"},
    )

    assert response.status_code == 401


def test_process_no_auth(client: TestClient) -> None:
    """Test process endpoint without auth returns 401."""
    response = client.post(
        "/process",
        json={
            "id": "tx_001",
            "tenant_id": "test_tenant",
            "amount": "100.50",
            "region": "EU",
            "timestamp": "2026-08-23T12:00:00Z",
        },
    )

    assert response.status_code == 401


def test_process_transaction_success(
    client: TestClient,
    valid_token: str,
) -> None:
    """Test successful transaction processing."""
    with patch.object(
        orchestrator,
        "process_batch",
        return_value=(1, 0),
    ):
        response = client.post(
            "/process",
            json={
                "id": "tx_001",
                "tenant_id": "test_tenant",
                "amount": "100.50",
                "region": "EU",
                "timestamp": "2026-08-23T12:00:00Z",
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["processed"] == 1
    assert data["failed"] == 0
    assert data["success_rate"] == 100.0


def test_process_tenant_mismatch(
    client: TestClient,
    valid_token: str,
) -> None:
    """Test transaction with mismatched tenant."""
    response = client.post(
        "/process",
        json={
            "id": "tx_001",
            "tenant_id": "wrong_tenant",
            "amount": "100.50",
            "region": "EU",
            "timestamp": "2026-08-23T12:00:00Z",
        },
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 403
    data = response.json()
    assert "Tenant mismatch" in data["detail"]


def test_process_missing_write_scope(
    client: TestClient,
) -> None:
    """Test process endpoint with read-only scope."""
    read_only_token = jwt_auth.create_token(
        user_id="read_user",
        tenant_id="test_tenant",
        scopes=["read"],
    )

    response = client.post(
        "/process",
        json={
            "id": "tx_001",
            "tenant_id": "test_tenant",
            "amount": "100.50",
            "region": "EU",
            "timestamp": "2026-08-23T12:00:00Z",
        },
        headers={"Authorization": f"Bearer {read_only_token}"},
    )

    assert response.status_code == 403
    data = response.json()
    assert "Missing write scope" in data["detail"]


def test_process_error_handling(
    client: TestClient,
    valid_token: str,
) -> None:
    """Test error handling in process endpoint."""
    with patch.object(
        orchestrator,
        "process_batch",
        side_effect=RuntimeError("Database connection failed"),
    ):
        response = client.post(
            "/process",
            json={
                "id": "tx_001",
                "tenant_id": "test_tenant",
                "amount": "100.50",
                "region": "EU",
                "timestamp": "2026-08-23T12:00:00Z",
            },
            headers={"Authorization": f"Bearer {valid_token}"},
        )

    assert response.status_code == 500
    data = response.json()
    assert "Database connection failed" in data["detail"]


def test_metrics_endpoint(client: TestClient) -> None:
    """Test metrics endpoint (no auth required)."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert b"# HELP" in response.content or len(response.content) > 0


def test_require_scope_decorator_missing_scope(client):
    """Test require_scope decorator rejects missing scope."""
    read_only_token = jwt_auth.create_token(
        user_id="user123",
        tenant_id="tenant_abc",
        scopes=["read"],  # No "write"
    )

    response = client.post(
        "/process",
        json={
            "id": "tx_001",
            "tenant_id": "tenant_abc",
            "amount": "100.50",
            "region": "EU",
            "timestamp": "2026-08-23T12:00:00Z",
        },
        headers={"Authorization": f"Bearer {read_only_token}"},
    )

    assert response.status_code == 403
    assert "Missing write scope" in response.json()["detail"]


def test_get_current_user_missing_header(client):
    """Test get_current_user without Authorization header."""
    response = client.get("/stats")

    assert response.status_code == 401
    assert "Missing authorization header" in response.json()["detail"]


def test_get_current_user_invalid_scheme(client):
    """Test get_current_user with wrong auth scheme."""
    response = client.get(
        "/stats",
        headers={"Authorization": "Basic abc123"},
    )

    assert response.status_code == 401
    assert "Invalid authorization scheme" in response.json()["detail"]


@pytest.fixture
def jwt_authenticator() -> JWTAuthenticator:
    """Create JWT authenticator."""
    secret = "test-secret-key-with-minimum-32-bytes-length"
    return JWTAuthenticator(
        secret_key=secret,
        algorithm="HS256",
    )


def test_process_admin_missing_admin_scope(client, valid_token):
    """Test admin endpoint rejects non-admin user."""
    # valid_token has ["read", "write"], not "admin"
    response = client.post(
        "/process-admin",
        json={
            "id": "tx_001",
            "tenant_id": "test_tenant",
            "amount": "100.50",
            "region": "EU",
            "timestamp": "2026-08-23T12:00:00Z",
        },
        headers={"Authorization": f"Bearer {valid_token}"},
    )

    assert response.status_code == 403
    assert "Missing required scope: admin" in response.json()["detail"]
    
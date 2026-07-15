import pytest


@pytest.fixture
def sample_transaction():
    """Sample transaction for testing"""
    return {
        "id": "tx_001",
        "tenant_id": "tenant_abc",
        "amount": 100.50,
        "region": "EU",
    }

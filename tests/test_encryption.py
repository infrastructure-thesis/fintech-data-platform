from src.audit.encryption import ComplianceHasher


def test_compute_hash():
    """Test hash computation is deterministic."""
    data = {
        "id": "tx_001",
        "tenant_id": "tenant_abc",
        "amount": "100.50",
        "timestamp": "2026-01-01T00:00:00",
    }

    hash1 = ComplianceHasher.compute_hash(data)
    hash2 = ComplianceHasher.compute_hash(data)

    # Same data should produce same hash
    assert hash1 == hash2
    # Hash should be 64 chars (SHA256)
    assert len(hash1) == 64


def test_verify_hash_valid():
    """Test hash verification succeeds with correct hash."""
    data = {
        "id": "tx_001",
        "tenant_id": "tenant_abc",
        "amount": "100.50",
        "timestamp": "2026-01-01T00:00:00",
    }

    correct_hash = ComplianceHasher.compute_hash(data)
    assert ComplianceHasher.verify_hash(data, correct_hash) is True


def test_verify_hash_invalid():
    """Test hash verification fails with wrong hash."""
    data = {
        "id": "tx_001",
        "tenant_id": "tenant_abc",
        "amount": "100.50",
        "timestamp": "2026-01-01T00:00:00",
    }

    zero_hash = "0" * 64
    assert ComplianceHasher.verify_hash(data, zero_hash) is False

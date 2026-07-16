import pytest
from datetime import datetime, timezone
from decimal import Decimal
from src.pipeline.models import Transaction, AuditLogEntry


def test_transaction_creation(sample_transaction):
    """Test creating a transaction"""
    tx = Transaction(
        id="tx_001",
        tenant_id="tenant_abc",
        amount=Decimal("100.50"),
        region="EU",
        timestamp=datetime.now(timezone.utc),
    )
    assert tx.id == "tx_001"
    assert tx.region == "EU"


def test_transaction_validation_success():
    """Test that valid transaction passes validation."""
    tx = Transaction(
        id="tx_001",
        tenant_id="tenant_abc",
        amount=Decimal("100.50"),
        region="EU",
        timestamp=datetime.now(timezone.utc),
    )
    tx.validate()  # Should not raise


def test_transaction_validation_empty_id():
    """Test that empty ID is rejected."""
    tx = Transaction(
        id="",
        tenant_id="tenant_abc",
        amount=Decimal("100.50"),
        region="EU",
        timestamp=datetime.now(timezone.utc),
    )
    with pytest.raises(ValueError) as exc_info:
        tx.validate()
    assert "Transaction ID cannot be empty" in str(exc_info.value)


def test_transaction_validation_invalid_amount():
    """Test that negative amounts are rejected."""
    tx = Transaction(
        id="tx_001",
        tenant_id="tenant_abc",
        amount=Decimal("-50.00"),
        region="EU",
        timestamp=datetime.now(timezone.utc),
    )
    with pytest.raises(ValueError) as exc_info:
        tx.validate()
    assert "Amount must be positive" in str(exc_info.value)


def test_transaction_validation_invalid_region():
    """Test that unknown regions are rejected."""
    tx = Transaction(
        id="tx_001",
        tenant_id="tenant_abc",
        amount=Decimal("100.50"),
        region="UNKNOWN",
        timestamp=datetime.now(timezone.utc),
    )
    with pytest.raises(ValueError) as exc_info:
        tx.validate()
    assert "Unknown region" in str(exc_info.value)


def test_audit_log_entry_from_transaction():
    """Test creating audit entry from transaction"""
    now = datetime.now(timezone.utc)
    tx = Transaction(
        id="tx_001",
        tenant_id="tenant_abc",
        amount=Decimal("100.50"),
        region="EU",
        timestamp=datetime.now(),
    )
    audit_entry = AuditLogEntry.from_transaction(tx, "abc123def456")

    assert audit_entry.transaction_id == "tx_001"
    assert audit_entry.compliance_hash == "abc123def456"
    assert audit_entry.tenant_id == "tenant_abc"
    assert audit_entry.amount == Decimal("100.50")
    assert audit_entry.region == "EU"

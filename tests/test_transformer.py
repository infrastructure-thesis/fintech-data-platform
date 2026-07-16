from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.pipeline.models import Transaction
from src.pipeline.transformer import SettlementTransformer


def test_transform_valid_transaction():
    """Test transforming valid transaction."""
    tx = Transaction(
        id="tx_001",
        tenant_id="tenant_abc",
        amount=Decimal("100.50"),
        region="EU",
        timestamp=datetime.now(timezone.utc),
    )

    audit_entry = SettlementTransformer.transform(tx)

    assert audit_entry.transaction_id == "tx_001"
    assert audit_entry.tenant_id == "tenant_abc"
    assert audit_entry.amount == Decimal("100.50")
    assert audit_entry.region == "EU"
    assert len(audit_entry.compliance_hash) == 64  # SHA256


def test_transform_invalid_region():
    """Test transforming transaction with invalid region."""
    tx = Transaction(
        id="tx_001",
        tenant_id="tenant_abc",
        amount=Decimal("100.50"),
        region="INVALID",
        timestamp=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError, match="Unknown region"):
        SettlementTransformer.transform(tx)


def test_transform_negative_amount():
    """Test transforming transaction with negative amount."""
    tx = Transaction(
        id="tx_001",
        tenant_id="tenant_abc",
        amount=Decimal("-50.00"),
        region="EU",
        timestamp=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError, match="Amount must be positive"):
        SettlementTransformer.transform(tx)


def test_transform_hash_deterministic():
    """Test that same transaction produces same hash."""
    tx = Transaction(
        id="tx_001",
        tenant_id="tenant_abc",
        amount=Decimal("100.50"),
        region="EU",
        timestamp=datetime.now(timezone.utc),
    )

    entry1 = SettlementTransformer.transform(tx)
    entry2 = SettlementTransformer.transform(tx)

    assert entry1.compliance_hash == entry2.compliance_hash
